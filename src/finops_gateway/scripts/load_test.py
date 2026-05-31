"""Concurrent load test for the query gateway (local, $0)."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from finops_gateway.config import load_settings, validate_gateway
from finops_gateway.eval.dataset import EvalDataset
from finops_gateway.scripts.query_gateway import run_gateway


@dataclass
class RequestResult:
    index: int
    question: str
    ok: bool
    latency_s: float
    tier: str = ""
    error: str = ""
    retrieval_latency_s: float = 0.0
    cost_usd: float = 0.0


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct / 100.0
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def _run_one(index: int, question: str, k: int) -> RequestResult:
    start = time.perf_counter()
    try:
        result = run_gateway(question, k)
        latency = time.perf_counter() - start
        return RequestResult(
            index=index,
            question=question,
            ok=True,
            latency_s=latency,
            tier=str(result["tier"]),
            retrieval_latency_s=float(result["retrieval_latency_s"]),
            cost_usd=float(result["usage"]["cost_usd"]),
        )
    except Exception as exc:
        return RequestResult(
            index=index,
            question=question,
            ok=False,
            latency_s=time.perf_counter() - start,
            error=f"{type(exc).__name__}: {exc}",
        )


def _load_questions(limit: int) -> list[str]:
    dataset = EvalDataset.load()
    return [pair.question for pair in dataset.pairs[:limit]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run concurrent gateway queries and report latency/errors."
    )
    parser.add_argument("--requests", type=int, default=15, help="Total queries.")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Parallel workers (keep low on 4GB VRAM).",
    )
    parser.add_argument("--k", type=int, default=4, help="Retrieval top-k.")
    parser.add_argument(
        "--output",
        default="",
        help="Write JSON summary (default: data/load_test_results.json).",
    )
    return parser.parse_args()


def format_summary(
    results: list[RequestResult], *, elapsed_s: float, concurrency: int
) -> str:
    ok = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    latencies = [r.latency_s for r in ok]
    tiers: dict[str, int] = {}
    for r in ok:
        tiers[r.tier] = tiers.get(r.tier, 0) + 1

    lines = [
        "# Gateway load test",
        "",
        f"- requests: {len(results)}",
        f"- concurrency: {concurrency}",
        f"- wall time: {elapsed_s:.1f}s",
        f"- success: {len(ok)} | failed: {len(failed)}",
        "",
    ]
    if latencies:
        lines.extend(
            [
                "## Latency (successful requests)",
                "",
                f"- mean: {statistics.mean(latencies):.2f}s",
                f"- p50: {_percentile(latencies, 50):.2f}s",
                f"- p95: {_percentile(latencies, 95):.2f}s",
                f"- max: {max(latencies):.2f}s",
                "",
            ]
        )
    if tiers:
        lines.append("## Routing tiers")
        lines.append("")
        for tier, count in sorted(tiers.items()):
            lines.append(f"- {tier}: {count}")
        lines.append("")
    if failed:
        lines.append("## Failures")
        lines.append("")
        for r in failed[:10]:
            lines.append(f"- #{r.index}: {r.error}")
        lines.append("")
    lines.append("_Metrics pushed to Pushgateway — check Grafana during/after the run._")
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    load_settings()
    validate_gateway()

    questions = _load_questions(max(args.requests, 1))
    if not questions:
        raise SystemExit("No eval questions found. Run finops-generate-eval-dataset first.")

    print(
        f"Load test: {args.requests} requests, concurrency={args.concurrency}, k={args.k}",
        flush=True,
    )

    start = time.perf_counter()
    results: list[RequestResult] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {
            pool.submit(_run_one, i, questions[i % len(questions)], args.k): i
            for i in range(args.requests)
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status = "OK" if result.ok else "FAIL"
            print(
                f"  [{status}] #{result.index} {result.latency_s:.1f}s "
                f"{result.tier or result.error[:60]}",
                flush=True,
            )

    elapsed = time.perf_counter() - start
    results.sort(key=lambda r: r.index)
    summary = format_summary(results, elapsed_s=elapsed, concurrency=args.concurrency)
    print("\n" + summary, flush=True)

    out_json = (
        Path(args.output)
        if args.output
        else Path(__file__).resolve().parents[3] / "data" / "load_test_results.json"
    )
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "requests": args.requests,
                "concurrency": args.concurrency,
                "elapsed_s": elapsed,
                "results": [asdict(r) for r in results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_md = out_json.with_suffix(".md")
    out_md.write_text(summary + "\n", encoding="utf-8")
    print(f"\nSaved {out_json} and {out_md}", flush=True)


if __name__ == "__main__":
    main()

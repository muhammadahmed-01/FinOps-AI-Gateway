"""Publish saved eval and load-test results to Pushgateway for Grafana."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from finops_gateway.config import load_settings
from finops_gateway.metrics import record_query_metrics, record_ragas_scores

DATA_ROOT = Path(__file__).resolve().parents[3] / "data"
DEFAULT_RAGAS = DATA_ROOT / "eval" / "ragas_results_8pair.json"
DEFAULT_LOAD = DATA_ROOT / "load_test_results.json"

# Placeholder token split when replaying load-test JSON (cost/routing panels only).
_DEFAULT_INPUT_TOKENS = 400
_DEFAULT_OUTPUT_TOKENS = 150


def load_ragas_scores(path: Path) -> tuple[dict[str, float], dict[str, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    baseline = payload["baseline"]
    hybrid = payload["hybrid"]
    metrics = ("faithfulness", "answer_relevancy", "context_precision")
    baseline_scores = {m: float(baseline[m]) for m in metrics}
    hybrid_scores = {m: float(hybrid[m]) for m in metrics}
    return baseline_scores, hybrid_scores


def replay_load_test(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    replayed = 0
    for row in payload.get("results", []):
        if not row.get("ok"):
            continue
        record_query_metrics(
            tier=str(row["tier"]),
            input_tokens=_DEFAULT_INPUT_TOKENS,
            output_tokens=_DEFAULT_OUTPUT_TOKENS,
            cost_usd=float(row.get("cost_usd", 0.0)),
            retrieval_latency_s=float(row.get("retrieval_latency_s", 0.0)),
        )
        replayed += 1
    return replayed


def publish_results(
    *,
    ragas_path: Path,
    load_path: Path | None,
    skip_load: bool,
) -> None:
    load_settings()
    baseline, hybrid = load_ragas_scores(ragas_path)
    record_ragas_scores("baseline", baseline)
    record_ragas_scores("hybrid", hybrid)

    replayed = 0
    if not skip_load and load_path is not None and load_path.is_file():
        replayed = replay_load_test(load_path)

    print(f"Published RAGAS scores from {ragas_path.name}")
    if skip_load:
        print("Skipped load-test replay (--skip-load)")
    elif replayed:
        print(f"Replayed {replayed} load-test requests from {load_path.name}")
    else:
        print(f"No load-test replay ({load_path} missing or empty)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Push saved RAGAS + load-test metrics to Pushgateway."
    )
    parser.add_argument(
        "--ragas",
        default=str(DEFAULT_RAGAS),
        help="Path to ragas_results_8pair.json",
    )
    parser.add_argument(
        "--load-test",
        default=str(DEFAULT_LOAD),
        help="Path to load_test_results.json for tier/cost replay",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Only publish RAGAS scores (skip load-test replay).",
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    ragas_path = Path(args.ragas)
    load_path = Path(args.load_test)

    if not ragas_path.is_file():
        raise SystemExit(f"RAGAS results not found: {ragas_path}")

    publish_results(
        ragas_path=ragas_path,
        load_path=load_path,
        skip_load=args.skip_load,
    )
    print("\nOpen Grafana: http://localhost:3001 (admin/admin)")
    print("Dashboard: FinOps AI Gateway")


if __name__ == "__main__":
    main()

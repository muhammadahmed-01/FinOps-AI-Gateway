"""Compute and summarize benchmark numbers from committed result files."""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "data"
LOAD_JSON = DATA / "load_test_results.json"
RAGAS_JSON = DATA / "eval" / "ragas_results_8pair.json"
OUTPUT = DATA / "RESULTS.md"


@dataclass
class Percentiles:
    p50: float
    p95: float
    mean: float
    max: float


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct / 100.0
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def _stats(values: list[float]) -> Percentiles:
    if not values:
        return Percentiles(0.0, 0.0, 0.0, 0.0)
    return Percentiles(
        p50=_percentile(values, 50),
        p95=_percentile(values, 95),
        mean=statistics.mean(values),
        max=max(values),
    )


def _fmt_seconds(value: float) -> str:
    if value >= 60:
        return f"{value:.1f}s ({value / 60:.1f} min)"
    return f"{value:.2f}s"


def _load_test_section(payload: dict) -> str:
    rows = [r for r in payload.get("results", []) if r.get("ok")]
    tiers: dict[str, int] = {}
    costs: list[float] = []
    total_lat: list[float] = []
    retrieval_lat: list[float] = []
    classification_lat: list[float] = []
    generation_lat: list[float] = []
    by_tier_gen: dict[str, list[float]] = {}

    for row in rows:
        tier = str(row["tier"])
        tiers[tier] = tiers.get(tier, 0) + 1
        costs.append(float(row.get("cost_usd", 0.0)))
        total_lat.append(float(row["latency_s"]))
        retrieval_lat.append(float(row.get("retrieval_latency_s", 0.0)))
        cls_lat = float(row.get("classification_latency_s", 0.0))
        gen_lat = float(row.get("generation_latency_s", 0.0))
        if cls_lat > 0:
            classification_lat.append(cls_lat)
        if gen_lat > 0:
            generation_lat.append(gen_lat)
            by_tier_gen.setdefault(tier, []).append(gen_lat)
        elif row.get("retrieval_latency_s") is not None:
            # Back-compat when only total + retrieval were recorded.
            approx = max(float(row["latency_s"]) - float(row["retrieval_latency_s"]), 0.0)
            generation_lat.append(approx)
            by_tier_gen.setdefault(tier, []).append(approx)

    n = len(rows)
    simple = tiers.get("simple", 0)
    simulated_total = sum(costs)
    complex_costs = [float(r["cost_usd"]) for r in rows if r["tier"] == "complex"]
    complex_avg = statistics.mean(complex_costs) if complex_costs else 0.0
    all_complex_counterfactual = complex_avg * n if complex_costs else 0.0
    savings_pct = 0.0
    if all_complex_counterfactual > 0:
        savings_pct = (1 - simulated_total / all_complex_counterfactual) * 100

    total_stats = _stats(total_lat)
    retrieval_stats = _stats(retrieval_lat)
    class_stats = _stats(classification_lat)
    gen_stats = _stats(generation_lat)

    lines = [
        "# Measured results (generated)",
        "",
        "_Do not edit by hand. Regenerate with `uv run finops-report-results`._",
        "",
        "## Load test",
        "",
        f"- Source: `{LOAD_JSON.as_posix()}`",
        f"- Requests: {payload.get('requests', n)} (successful: {n})",
        f"- Concurrency: {payload.get('concurrency', '?')}",
        f"- Wall time: {_fmt_seconds(float(payload.get('elapsed_s', 0.0)))}",
        "",
        "### Routing (measured)",
        "",
    ]
    for tier, count in sorted(tiers.items()):
        pct = (count / n * 100) if n else 0
        lines.append(f"- {tier}: {count}/{n} ({pct:.0f}%)")
    lines.extend(
        [
            "",
            "### End-to-end latency (measured, wall clock per request)",
            "",
            f"- p50: {_fmt_seconds(total_stats.p50)}",
            f"- p95: {_fmt_seconds(total_stats.p95)}",
            f"- mean: {_fmt_seconds(total_stats.mean)}",
            f"- max: {_fmt_seconds(total_stats.max)}",
            "",
            "### Latency breakdown (measured)",
            "",
            f"- Retrieval p50: {_fmt_seconds(retrieval_stats.p50)}",
        ]
    )
    if classification_lat:
        lines.append(f"- Classification p50: {_fmt_seconds(class_stats.p50)}")
    else:
        lines.append(
            "- Classification: _not recorded in this JSON (re-run load test after upgrade)_"
        )
    lines.append(f"- Generation p50 (all tiers): {_fmt_seconds(gen_stats.p50)}")
    for tier in ("simple", "medium", "complex"):
        if tier in by_tier_gen:
            tier_stats = _stats(by_tier_gen[tier])
            lines.append(
                f"- Generation p50 ({tier} tier): {_fmt_seconds(tier_stats.p50)}"
            )
    lines.extend(
        [
            "",
            "### Cost (simulated FinOps model — not actual API spend)",
            "",
            "Grafana cost uses **Claude list prices × token counts** from the router. "
            "In default demo mode, medium/complex answers run on **Groq (free)** and "
            "simple on **Ollama (local)** — **actual API spend was $0**.",
            "",
            f"- Simulated spend with tier routing: **${simulated_total:.4f}** ({n} queries)",
            f"- Simulated counterfactual (all {n} queries at avg complex-tier rate): "
            f"**${all_complex_counterfactual:.4f}**",
        ]
    )
    if all_complex_counterfactual > 0:
        lines.append(
            f"- Modeled savings vs all-complex counterfactual: **{savings_pct:.0f}%** "
            "(simulation only)"
        )
    lines.append("")
    return "\n".join(lines)


def _ragas_section(payload: dict) -> str:
    baseline = payload["baseline"]
    hybrid = payload["hybrid"]
    meta = payload.get("methodology", {})
    n = payload.get("sample_count", meta.get("sample_count", "?"))
    lines = [
        "",
        "## RAGAS pilot eval (n=8)",
        "",
        f"- Source: `{RAGAS_JSON.as_posix()}`",
        f"- Sample size: **{n}** Q&A pairs (pilot — not statistically powered)",
        f"- Judge (faithfulness, context_precision): {meta.get('judge', 'see JSON')}",
        f"- Answer generation: {meta.get('answer_model', 'see JSON')}",
        f"- answer_relevancy: {meta.get('answer_relevancy', 'embedding cosine proxy')}",
        "",
        "| Metric | Baseline | Hybrid+rerank | Delta |",
        "|--------|----------|---------------|-------|",
    ]
    for metric in ("context_precision", "faithfulness", "answer_relevancy"):
        b = float(baseline[metric])
        h = float(hybrid[metric])
        delta = h - b
        sign = "+" if delta >= 0 else ""
        lines.append(f"| {metric} | {b:.4f} | {h:.4f} | {sign}{delta:.4f} |")
    lines.extend(
        [
            "",
            "**Interpretation:** The reliable signal at n=8 is **context_precision** "
            "(retrieval quality). Treat **faithfulness** at 1.0000 as high-variance at "
            "small n — do not over-claim.",
            "",
            meta.get("limitations", ""),
        ]
    )
    return "\n".join(line for line in lines if line is not None)


def build_results_markdown() -> str:
    load_payload = json.loads(LOAD_JSON.read_text(encoding="utf-8"))
    ragas_payload = json.loads(RAGAS_JSON.read_text(encoding="utf-8"))
    return _load_test_section(load_payload) + _ragas_section(ragas_payload) + "\n"


def write_results_markdown(path: Path | None = None) -> Path:
    out = path or OUTPUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_results_markdown(), encoding="utf-8")
    return out


def main() -> None:
    path = write_results_markdown()
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

"""Tests for RAGAS comparison helpers."""

from __future__ import annotations

from finops_gateway.eval.ragas_runner import PipelineScores, format_comparison_table


def test_format_comparison_table_includes_metrics() -> None:
    baseline = PipelineScores(
        pipeline="baseline",
        faithfulness=0.7,
        answer_relevancy=0.8,
        context_precision=0.6,
        sample_count=10,
    )
    hybrid = PipelineScores(
        pipeline="hybrid",
        faithfulness=0.75,
        answer_relevancy=0.82,
        context_precision=0.72,
        sample_count=10,
    )
    table = format_comparison_table(baseline, hybrid)
    assert "context_precision" in table
    assert "0.7200" in table
    assert "+0.1200" in table

"""Tests for report_results markdown generation."""

from __future__ import annotations

import json
from pathlib import Path

from finops_gateway.scripts.report_results import build_results_markdown, write_results_markdown


def test_build_results_markdown_includes_measured_and_simulated(tmp_path: Path) -> None:
    load = tmp_path / "load.json"
    load.write_text(
        json.dumps(
            {
                "requests": 2,
                "concurrency": 1,
                "elapsed_s": 10.0,
                "results": [
                    {
                        "ok": True,
                        "tier": "simple",
                        "latency_s": 100.0,
                        "retrieval_latency_s": 2.0,
                        "generation_latency_s": 97.0,
                        "cost_usd": 0.0,
                    },
                    {
                        "ok": True,
                        "tier": "complex",
                        "latency_s": 5.0,
                        "retrieval_latency_s": 2.0,
                        "generation_latency_s": 2.5,
                        "classification_latency_s": 0.5,
                        "cost_usd": 0.01,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    ragas = tmp_path / "ragas.json"
    ragas.write_text(
        json.dumps(
            {
                "sample_count": 8,
                "methodology": {
                    "judge": "groq",
                    "answer_model": "ollama",
                    "answer_relevancy": "embedding",
                    "limitations": "pilot",
                },
                "baseline": {
                    "faithfulness": 0.7,
                    "answer_relevancy": 0.7,
                    "context_precision": 0.6,
                },
                "hybrid": {
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.72,
                    "context_precision": 0.72,
                },
            }
        ),
        encoding="utf-8",
    )

    from finops_gateway.scripts import report_results as mod

    original_load = mod.LOAD_JSON
    original_ragas = mod.RAGAS_JSON
    mod.LOAD_JSON = load
    mod.RAGAS_JSON = ragas
    try:
        text = build_results_markdown()
    finally:
        mod.LOAD_JSON = original_load
        mod.RAGAS_JSON = original_ragas

    assert "simulated FinOps model" in text
    assert "not actual API spend" in text
    assert "pilot" in text.lower()
    assert "Generation p50 (simple tier)" in text


def test_write_results_markdown(tmp_path: Path) -> None:
    out = tmp_path / "RESULTS.md"
    from finops_gateway.scripts import report_results as mod

    original_out = mod.OUTPUT
    mod.OUTPUT = out
    try:
        path = write_results_markdown()
    finally:
        mod.OUTPUT = original_out
    assert path.exists()

"""Tests for publish_results helpers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from finops_gateway.scripts.publish_results import load_ragas_scores, publish_results


def test_load_ragas_scores(tmp_path: Path) -> None:
    path = tmp_path / "ragas.json"
    path.write_text(
        json.dumps(
            {
                "baseline": {
                    "faithfulness": 0.77,
                    "answer_relevancy": 0.77,
                    "context_precision": 0.6,
                },
                "hybrid": {
                    "faithfulness": 1.0,
                    "answer_relevancy": 0.79,
                    "context_precision": 0.79,
                },
            }
        ),
        encoding="utf-8",
    )
    baseline, hybrid = load_ragas_scores(path)
    assert baseline["context_precision"] == 0.6
    assert hybrid["context_precision"] == 0.79


def test_publish_results_calls_metrics(tmp_path: Path) -> None:
    ragas = tmp_path / "ragas.json"
    ragas.write_text(
        json.dumps(
            {
                "baseline": {
                    "faithfulness": 0.77,
                    "answer_relevancy": 0.77,
                    "context_precision": 0.6,
                },
                "hybrid": {
                    "faithfulness": 1.0,
                    "answer_relevancy": 0.79,
                    "context_precision": 0.79,
                },
            }
        ),
        encoding="utf-8",
    )
    load = tmp_path / "load.json"
    load.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "ok": True,
                        "tier": "simple",
                        "cost_usd": 0.0,
                        "retrieval_latency_s": 1.2,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with (
        patch("finops_gateway.scripts.publish_results.load_settings"),
        patch("finops_gateway.scripts.publish_results.record_ragas_scores") as ragas_mock,
        patch(
            "finops_gateway.scripts.publish_results.record_query_metrics"
        ) as query_mock,
    ):
        publish_results(ragas_path=ragas, load_path=load, skip_load=False)

    assert ragas_mock.call_count == 2
    query_mock.assert_called_once()

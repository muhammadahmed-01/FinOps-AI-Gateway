"""Tests for classifier fallback behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from finops_gateway.routing.classifier import ComplexityResult, classify_complexity


def test_classify_complexity_defaults_on_llm_failure() -> None:
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = RuntimeError("rate limit")

    with patch(
        "finops_gateway.routing.classifier._build_classifier_llm",
        return_value=MagicMock(with_structured_output=lambda _: mock_llm),
    ):
        result = classify_complexity("What is LangGraph?")

    assert result.tier == "medium"
    assert result.needs_human_review is True
    assert "defaulting to medium tier" in result.reasoning


def test_classify_complexity_parses_valid_result() -> None:
    expected = ComplexityResult(
        tier="simple",
        complexity_score=0.1,
        reasoning="Single fact lookup.",
    )
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = expected

    with patch(
        "finops_gateway.routing.classifier._build_classifier_llm",
        return_value=MagicMock(with_structured_output=lambda _: mock_llm),
    ):
        result = classify_complexity("What is LangGraph?")

    assert result.tier == "simple"
    assert result.needs_human_review is False

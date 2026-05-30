"""Tests for cost estimation and token usage extraction."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from finops_gateway.routing.pricing import estimate_cost_usd, extract_token_usage


def test_estimate_cost_simple_tier_is_zero() -> None:
    assert estimate_cost_usd("simple", 500, 200) == 0.0


def test_estimate_cost_medium_tier() -> None:
    # Haiku 4.5: $1/MTok in, $5/MTok out
    cost = estimate_cost_usd("medium", 1_000, 500)
    assert cost == pytest.approx(0.001 + 0.0025)


def test_estimate_cost_complex_tier() -> None:
    # Sonnet 4.5: $3/MTok in, $15/MTok out
    cost = estimate_cost_usd("complex", 1_000, 500)
    assert cost == pytest.approx(0.003 + 0.0075)


def test_extract_token_usage_from_usage_metadata() -> None:
    response = SimpleNamespace(
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    )
    usage = extract_token_usage(response)
    assert usage == {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}


def test_extract_token_usage_from_response_metadata() -> None:
    response = SimpleNamespace(
        usage_metadata=None,
        response_metadata={
            "token_usage": {"prompt_tokens": 20, "completion_tokens": 8}
        },
    )
    usage = extract_token_usage(response)
    assert usage["input_tokens"] == 20
    assert usage["output_tokens"] == 8
    assert usage["total_tokens"] == 28


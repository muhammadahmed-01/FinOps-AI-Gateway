"""Token usage extraction and per-tier cost estimation.

IMPORTANT — demo vs live:
- Grafana ``finops_cost_dollars_total`` uses Claude list prices × token counts (FinOps model).
- Demo mode (no real ANTHROPIC_API_KEY): medium/complex answers use Groq; actual spend is $0.
- Live mode: medium/complex use Claude; Grafana cost tracks the same formula on real tokens.

Rates: https://platform.claude.com/docs/en/about-claude/pricing
"""

from __future__ import annotations

from typing import Any

from finops_gateway.routing.classifier import RoutingTier

# USD per token — Claude API list prices (March 2026 docs)
# Haiku 4.5:  $1 / MTok in,  $5 / MTok out
# Sonnet 4.5: $3 / MTok in, $15 / MTok out
TIER_PRICING: dict[RoutingTier, tuple[float, float]] = {
    "simple": (0.0, 0.0),
    "medium": (1.0 / 1_000_000, 5.0 / 1_000_000),
    "complex": (3.0 / 1_000_000, 15.0 / 1_000_000),
}


def extract_token_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage_metadata", None) or {}
    if usage:
        return {
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
        }

    meta = getattr(response, "response_metadata", {}) or {}
    token_usage = meta.get("token_usage") or meta.get("usage") or {}
    input_tokens = int(
        token_usage.get("prompt_tokens")
        or token_usage.get("input_tokens")
        or 0
    )
    output_tokens = int(
        token_usage.get("completion_tokens")
        or token_usage.get("output_tokens")
        or 0
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def estimate_cost_usd(
    tier: RoutingTier, input_tokens: int, output_tokens: int
) -> float:
    input_rate, output_rate = TIER_PRICING[tier]
    return (input_tokens * input_rate) + (output_tokens * output_rate)

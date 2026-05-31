"""Prometheus metrics for FinOps AI Gateway."""

from __future__ import annotations

import os

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, pushadd_to_gateway

REGISTRY = CollectorRegistry()

ROUTING_TIER = Counter(
    "finops_routing_tier_total",
    "Routing decisions by tier",
    ["tier"],
    registry=REGISTRY,
)
COST_DOLLARS = Counter(
    "finops_cost_dollars_total",
    "Estimated query cost in USD",
    ["tier"],
    registry=REGISTRY,
)
TOKENS_USED = Counter(
    "finops_tokens_used_total",
    "Tokens consumed by routed answers",
    ["tier", "direction"],
    registry=REGISTRY,
)
RETRIEVAL_LATENCY = Histogram(
    "finops_retrieval_latency_seconds",
    "End-to-end hybrid retrieval latency",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=REGISTRY,
)
RAGAS_SCORE = Gauge(
    "finops_ragas_score",
    "Latest RAGAS evaluation score (0-1)",
    ["pipeline", "metric"],
    registry=REGISTRY,
)


def push_metrics() -> None:
    gateway = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091").rstrip("/")
    pushadd_to_gateway(
        gateway,
        job="finops-gateway",
        registry=REGISTRY,
    )


def record_query_metrics(
    *,
    tier: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    retrieval_latency_s: float,
) -> None:
    ROUTING_TIER.labels(tier=tier).inc()
    COST_DOLLARS.labels(tier=tier).inc(cost_usd)
    TOKENS_USED.labels(tier=tier, direction="input").inc(input_tokens)
    TOKENS_USED.labels(tier=tier, direction="output").inc(output_tokens)
    RETRIEVAL_LATENCY.observe(retrieval_latency_s)
    push_metrics()


def record_ragas_scores(pipeline: str, scores: dict[str, float]) -> None:
    for metric, value in scores.items():
        RAGAS_SCORE.labels(pipeline=pipeline, metric=metric).set(value)
    push_metrics()

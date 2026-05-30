"""Run simple, medium, and complex queries in one metrics session for Grafana."""

from __future__ import annotations

import os
import sys

from finops_gateway.config import load_settings, validate_gateway
from finops_gateway.scripts.query_gateway import run_gateway

TIER_QUESTIONS = {
    "simple": "What is a race condition?",
    "medium": (
        "Compare pessimistic locking and optimistic concurrency control. "
        "When should I use each?"
    ),
    "complex": (
        "Design a LangGraph architecture for a multi-agent research workflow "
        "with checkpointing, human-in-the-loop approval, and fallback routing "
        "when tool calls fail. Explain tradeoffs."
    ),
}


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    _configure_stdout()
    load_settings()
    validate_gateway()

    print("Pushing metrics to Pushgateway after each query...\n")

    results = []
    for label, question in TIER_QUESTIONS.items():
        print(f"=== {label.upper()} query ===")
        print(f"Q: {question[:80]}...")
        try:
            result = run_gateway(question, k=4)
            results.append(result)
            print(
                f"  routed={result['tier']} "
                f"score={result['complexity_score']:.2f} "
                f"cost=${result['usage']['cost_usd']:.6f} "
                f"tokens={result['usage']['total_tokens']}"
            )
        except Exception as exc:
            print(f"  FAILED: {exc}")
        print()

    print("Summary:")
    for result in results:
        print(
            f"  {result['tier']:7s} ${result['usage']['cost_usd']:.6f} "
            f"({result['usage']['total_tokens']} tokens)"
        )

    print("\nDone — open Grafana: http://localhost:3001")


if __name__ == "__main__":
    main()

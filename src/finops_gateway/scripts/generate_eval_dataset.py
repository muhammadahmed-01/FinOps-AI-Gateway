"""Generate 50 Q&A evaluation pairs from ingested LangGraph docs."""

from __future__ import annotations

import argparse
import sys

from finops_gateway.config import load_settings, validate_database, validate_embeddings
from finops_gateway.eval.dataset import DEFAULT_DATASET_PATH
from finops_gateway.eval.generate import generate_eval_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate LangGraph Q&A eval dataset using an LLM."
    )
    parser.add_argument("--count", type=int, default=50, help="Number of Q&A pairs.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for chunk sampling.")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    load_settings()
    validate_database()
    validate_embeddings()

    args = parse_args()
    dataset = generate_eval_dataset(count=args.count, seed=args.seed)
    path = dataset.save(DEFAULT_DATASET_PATH)
    print(f"Wrote {len(dataset.pairs)} Q&A pairs to {path}")


if __name__ == "__main__":
    main()

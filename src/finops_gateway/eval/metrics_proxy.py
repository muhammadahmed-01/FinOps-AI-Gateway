"""Lightweight metrics when full RAGAS LLM judges are unavailable."""

from __future__ import annotations

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embedding_answer_relevancy(
    question: str, answer: str, embedder
) -> float:
    """Cosine similarity between question and answer embeddings (0-1 scale)."""
    q_vec = embedder.embed_query(question)
    a_vec = embedder.embed_query(answer)
    return max(0.0, min(1.0, cosine_similarity(q_vec, a_vec)))

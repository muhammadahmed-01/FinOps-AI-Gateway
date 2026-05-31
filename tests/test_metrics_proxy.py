"""Tests for embedding relevancy proxy."""

from __future__ import annotations

from finops_gateway.eval.metrics_proxy import cosine_similarity, embedding_answer_relevancy


class StubEmbedder:
    def embed_query(self, text: str) -> list[float]:
        if "hello" in text.lower():
            return [1.0, 0.0]
        if "hi" in text.lower():
            return [0.9, 0.1]
        return [0.0, 1.0]


def test_cosine_similarity_identical() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_embedding_answer_relevancy_high_for_similar() -> None:
    score = embedding_answer_relevancy("hello world", "hi there", StubEmbedder())
    assert score > 0.8

"""Cross-encoder reranking for hybrid retrieval."""

from __future__ import annotations

from finops_gateway.rag.db import RetrievedChunk

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_cross_encoder = None


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder

        _cross_encoder = CrossEncoder(_MODEL_NAME)
    return _cross_encoder


def rerank(
    query: str, candidates: list[RetrievedChunk], *, top_k: int
) -> list[RetrievedChunk]:
    if not candidates:
        return []

    model = _get_cross_encoder()
    pairs = [[query, chunk.content] for chunk in candidates]
    scores = model.predict(pairs)

    ranked = sorted(
        zip(candidates, scores, strict=True),
        key=lambda item: float(item[1]),
        reverse=True,
    )
    return [
        RetrievedChunk(
            id=chunk.id,
            url=chunk.url,
            title=chunk.title,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=float(score),
        )
        for chunk, score in ranked[:top_k]
    ]

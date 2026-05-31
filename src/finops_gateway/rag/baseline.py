"""Cosine-similarity-only retrieval baseline for RAG evaluation."""

from __future__ import annotations

import time
from dataclasses import dataclass

from langsmith import traceable

from finops_gateway.embeddings import build_embeddings
from finops_gateway.rag.db import get_connection, query_similar_chunks
from finops_gateway.rag.hybrid import HybridRetrievalResult


@traceable(name="baseline_retrieve")
def baseline_retrieve(query: str, *, k: int = 4) -> HybridRetrievalResult:
    start = time.perf_counter()
    embeddings = build_embeddings()
    query_embedding = embeddings.embed_query(query)

    with get_connection() as conn:
        chunks = query_similar_chunks(conn, query_embedding, k)
        if not chunks:
            raise RuntimeError("No chunks in database. Run ingestion first.")

    latency = time.perf_counter() - start
    return HybridRetrievalResult(chunks=chunks, retrieval_latency_s=latency)

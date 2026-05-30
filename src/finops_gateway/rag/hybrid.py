"""Hybrid retrieval: pgvector + BM25 fused with RRF."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from langsmith import traceable

from finops_gateway.embeddings import build_embeddings
from finops_gateway.rag.db import ChunkRecord, RetrievedChunk, get_connection, query_similar_chunks
from finops_gateway.rag.reranker import rerank


@dataclass
class HybridRetrievalResult:
    chunks: list[RetrievedChunk]
    retrieval_latency_s: float


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _rrf_fuse(rankings: list[list[int]], *, k: int = 60) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


def _bm25_rank(query: str, corpus: list[ChunkRecord], top_n: int) -> list[int]:
    tokenized_corpus = [_tokenize(f"{row.title} {row.content}") for row in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [corpus[i].id for i in ranked[:top_n]]


@traceable(name="hybrid_retrieve")
def hybrid_retrieve(
    query: str,
    *,
    final_k: int = 4,
    candidate_k: int = 20,
    rrf_k: int = 60,
) -> HybridRetrievalResult:
    import time

    start = time.perf_counter()
    embeddings = build_embeddings()
    query_embedding = embeddings.embed_query(query)

    with get_connection() as conn:
        corpus = ChunkRecord.fetch_all(conn)
        if not corpus:
            raise RuntimeError("No chunks in database. Run ingestion first.")

        vector_hits = query_similar_chunks(conn, query_embedding, candidate_k)
        vector_ranking = [hit.id for hit in vector_hits]
        bm25_ranking = _bm25_rank(query, corpus, candidate_k)

    fused_scores = _rrf_fuse([vector_ranking, bm25_ranking], k=rrf_k)
    fused_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:candidate_k]

    id_to_chunk = {row.id: row for row in corpus}
    candidates = [
        RetrievedChunk(
            id=chunk_id,
            url=id_to_chunk[chunk_id].url,
            title=id_to_chunk[chunk_id].title,
            chunk_index=id_to_chunk[chunk_id].chunk_index,
            content=id_to_chunk[chunk_id].content,
            score=fused_scores[chunk_id],
        )
        for chunk_id in fused_ids
        if chunk_id in id_to_chunk
    ]

    reranked = rerank(query, candidates, top_k=final_k)
    latency = time.perf_counter() - start
    return HybridRetrievalResult(chunks=reranked, retrieval_latency_s=latency)

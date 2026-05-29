"""Ingest LangGraph docs into Postgres + pgvector."""

from __future__ import annotations

import os

from langsmith import traceable

from finops_gateway.config import (
    load_settings,
    validate_database,
    validate_embeddings,
    validate_langsmith,
)
from finops_gateway.embeddings import build_embeddings
from finops_gateway.ingestion.langgraph_docs import chunk_text, crawl_langgraph_docs
from finops_gateway.rag.db import clear_source, ensure_schema, get_connection, insert_chunk

SOURCE_NAME = "langgraph-docs"


@traceable(name="crawl_langgraph_docs")
def crawl(max_pages: int) -> list[dict]:
    return crawl_langgraph_docs(max_pages=max_pages)


def main() -> None:
    load_settings()
    validate_langsmith()
    validate_database()
    validate_embeddings()

    max_pages = int(os.getenv("INGEST_MAX_PAGES", "25"))
    embeddings = build_embeddings()
    pages = crawl(max_pages=max_pages)

    chunks: list[dict] = []
    for page in pages:
        text_chunks = chunk_text(page["text"])
        for idx, text in enumerate(text_chunks):
            chunks.append(
                {
                    "url": page["url"],
                    "title": page["title"],
                    "chunk_index": idx,
                    "content": text,
                }
            )

    if not chunks:
        raise RuntimeError("No chunks produced from LangGraph docs crawl.")

    vectors = embeddings.embed_documents([chunk["content"] for chunk in chunks])

    with get_connection() as conn:
        ensure_schema(conn)
        clear_source(conn, SOURCE_NAME)
        for chunk, vector in zip(chunks, vectors, strict=True):
            insert_chunk(
                conn,
                source=SOURCE_NAME,
                url=chunk["url"],
                title=chunk["title"],
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=vector,
                metadata={"source": SOURCE_NAME},
            )
        conn.commit()

    print(
        f"Ingested {len(chunks)} chunks from {len(pages)} pages into Postgres pgvector."
    )


if __name__ == "__main__":
    main()

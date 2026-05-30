"""Minimal retrieval + answer pipeline over pgvector chunks."""

from __future__ import annotations

import argparse
import os
import sys

from langchain_core.messages import HumanMessage
from langsmith import traceable

from finops_gateway.config import (
    load_settings,
    validate_database,
    validate_embeddings,
    validate_langsmith,
    validate_smoke_llm,
)
from finops_gateway.embeddings import build_embeddings
from finops_gateway.llm import build_smoke_llm
from finops_gateway.rag.db import get_connection, query_similar_chunks


@traceable(name="retrieve_chunks")
def retrieve(query: str, k: int) -> tuple[list, list[float]]:
    embeddings = build_embeddings()
    query_embedding = embeddings.embed_query(query)
    with get_connection() as conn:
        rows = query_similar_chunks(conn, query_embedding, k)
    return rows, query_embedding


@traceable(name="answer_from_context")
def answer(question: str, context_blocks: list[str]) -> str:
    llm = build_smoke_llm()
    context = "\n\n".join(context_blocks)
    prompt = (
        "You are a helpful assistant answering questions about LangGraph.\n"
        "Use only the provided context. If unsure, say you do not know.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer concisely and include references in plain text."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return str(response.content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query my personal blog.")
    parser.add_argument(
        "--question",
        default="Why did a race condition occur in my concurrency test and what's the best way to handle that to preserve integrity of data?",
        help="Question to ask the RAG system.",
    )
    parser.add_argument("--k", type=int, default=4, help="Number of chunks to retrieve.")
    return parser.parse_args()


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    _configure_stdout()
    load_settings()
    validate_langsmith()
    validate_database()
    validate_embeddings()
    validate_smoke_llm()

    args = parse_args()
    rows, _ = retrieve(args.question, args.k)
    if not rows:
        raise RuntimeError("No chunks found. Run ingestion first.")

    context_blocks = [
        f"[{idx + 1}] {row.title} ({row.url})\n{row.content[:1000]}"
        for idx, row in enumerate(rows)
    ]
    response = answer(args.question, context_blocks)

    print("\nAnswer:\n")
    print(response)
    print("\nTop sources:")
    for row in rows:
        print(f"- {row.title} :: {row.url} (score={row.score:.4f})")
    print(
        "\nTrace project: "
        f"{os.getenv('LANGCHAIN_PROJECT', 'default')} "
        "(check retrieve_chunks and answer_from_context spans)"
    )


if __name__ == "__main__":
    main()

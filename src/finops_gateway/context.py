"""Context assembly helpers for RAG prompts."""

from __future__ import annotations

from finops_gateway.llm_settings import context_char_budget_per_chunk
from finops_gateway.rag.db import RetrievedChunk


def truncate_to_budget(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_sentence = cut.rfind(". ")
    if last_sentence >= max_chars // 2:
        return cut[: last_sentence + 1]
    return cut.rstrip() + "..."


def build_context_blocks(
    chunks: list[RetrievedChunk],
    *,
    char_budget: int | None = None,
) -> list[str]:
    budget = char_budget if char_budget is not None else context_char_budget_per_chunk()
    return [
        f"[{idx + 1}] {row.title} ({row.url})\n{truncate_to_budget(row.content, budget)}"
        for idx, row in enumerate(chunks)
    ]

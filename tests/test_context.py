"""Tests for context truncation and block assembly."""

from __future__ import annotations

from finops_gateway.context import build_context_blocks, truncate_to_budget
from finops_gateway.rag.db import RetrievedChunk


def test_truncate_to_budget_keeps_short_text() -> None:
    assert truncate_to_budget("hello", 100) == "hello"


def test_truncate_to_budget_prefers_sentence_boundary() -> None:
    text = "First sentence. Second sentence is much longer than the first."
    result = truncate_to_budget(text, 20)
    assert result.endswith(".")
    assert len(result) <= 20


def test_build_context_blocks_respects_budget(monkeypatch) -> None:
    monkeypatch.setenv("CONTEXT_CHAR_BUDGET_PER_CHUNK", "50")
    chunks = [
        RetrievedChunk(
            id=1,
            url="https://example.com",
            title="Title",
            chunk_index=0,
            content="A" * 200,
            score=0.9,
        )
    ]
    blocks = build_context_blocks(chunks)
    assert len(blocks) == 1
    assert len(blocks[0]) < 200

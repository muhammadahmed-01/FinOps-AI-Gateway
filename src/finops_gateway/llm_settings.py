"""Shared LLM client settings (timeouts, retries, token limits)."""

from __future__ import annotations

import os


def llm_timeout_s() -> float:
    return float(os.getenv("LLM_TIMEOUT_S", "60"))


def llm_max_retries() -> int:
    return int(os.getenv("LLM_MAX_RETRIES", "2"))


def llm_max_tokens() -> int:
    return int(os.getenv("LLM_MAX_TOKENS", "1024"))


def context_char_budget_per_chunk() -> int:
    """Rough ~300 tokens per chunk at 4 chars/token."""
    return int(os.getenv("CONTEXT_CHAR_BUDGET_PER_CHUNK", "1200"))

"""Shared LLM client settings (timeouts, retries, token limits)."""

from __future__ import annotations

import os


def llm_timeout_s() -> float:
    return float(os.getenv("LLM_TIMEOUT_S", "60"))


def ragas_timeout_s() -> float:
    return float(os.getenv("RAGAS_TIMEOUT_S", "900"))


def eval_llm_timeout_s() -> float:
    """Longer timeout for batch eval on local GPU (default 60s is too short)."""
    return float(os.getenv("EVAL_LLM_TIMEOUT_S", os.getenv("LLM_TIMEOUT_S", "300")))


def llm_max_retries() -> int:
    return int(os.getenv("LLM_MAX_RETRIES", "2"))


def llm_max_tokens() -> int:
    return int(os.getenv("LLM_MAX_TOKENS", "1024"))


def context_char_budget_per_chunk() -> int:
    """Rough ~300 tokens per chunk at 4 chars/token."""
    return int(os.getenv("CONTEXT_CHAR_BUDGET_PER_CHUNK", "1200"))

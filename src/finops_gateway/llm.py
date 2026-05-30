"""LLM factory for smoke tests and early development."""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

from finops_gateway.llm_settings import llm_max_retries, llm_max_tokens, llm_timeout_s

SmokeProvider = Literal["ollama", "groq", "openai", "anthropic"]

_DEFAULT_OLLAMA_MODEL = "llama3.2"
_DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
_DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5"


def get_smoke_provider() -> SmokeProvider:
    provider = os.getenv("SMOKE_LLM_PROVIDER", "ollama").strip().lower()
    if provider not in ("ollama", "groq", "openai", "anthropic"):
        raise RuntimeError(
            f"Invalid SMOKE_LLM_PROVIDER: {provider!r}\n"
            "Use one of: ollama, groq, openai, anthropic"
        )
    return provider  # type: ignore[return-value]


def build_smoke_llm() -> BaseChatModel:
    """Return a chat model for the LangSmith trace smoke test."""
    provider = get_smoke_provider()
    timeout = llm_timeout_s()
    max_retries = llm_max_retries()

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
            timeout=timeout,
            num_retries=max_retries,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", _DEFAULT_GROQ_MODEL),
            temperature=0,
            timeout=timeout,
            max_retries=max_retries,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            timeout=timeout,
            max_retries=max_retries,
        )

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", _DEFAULT_ANTHROPIC_MODEL),
        temperature=0,
        max_tokens=llm_max_tokens(),
        timeout=timeout,
        max_retries=max_retries,
    )

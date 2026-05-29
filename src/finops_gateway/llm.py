"""LLM factory for smoke tests and early development."""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

SmokeProvider = Literal["ollama", "groq", "openai", "anthropic"]

_DEFAULT_OLLAMA_MODEL = "llama3.2"
_DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


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

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", _DEFAULT_GROQ_MODEL),
            temperature=0,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
        temperature=0,
    )

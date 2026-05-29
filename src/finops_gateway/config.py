"""Environment configuration and validation."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from finops_gateway.llm import SmokeProvider, get_smoke_provider

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


def load_settings() -> None:
    """Load .env from project root if present."""
    load_dotenv(_ENV_FILE)


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}\n"
            f"Copy .env.example to .env and set your keys."
        )
    return value


_UI_ENDPOINT_MARKERS = (
    "://smith.langchain.com",
    "://eu.smith.langchain.com",
    "://apac.smith.langchain.com",
    "://aws.smith.langchain.com",
)


def validate_langsmith_endpoint() -> None:
    """Reject dashboard URLs mistakenly used as LANGCHAIN_ENDPOINT."""
    endpoint = os.getenv("LANGCHAIN_ENDPOINT", "").strip().rstrip("/")
    if not endpoint:
        return
    if any(marker in endpoint for marker in _UI_ENDPOINT_MARKERS):
        raise RuntimeError(
            "LANGCHAIN_ENDPOINT must be the LangSmith API URL, not the dashboard.\n"
            "EU:  https://eu.api.smith.langchain.com\n"
            "US:  https://api.smith.langchain.com (or omit LANGCHAIN_ENDPOINT)"
        )


def validate_langsmith() -> None:
    """Ensure LangSmith tracing is configured."""
    _require("LANGCHAIN_API_KEY")
    validate_langsmith_endpoint()
    tracing = os.getenv("LANGCHAIN_TRACING_V2", "").lower()
    if tracing not in ("true", "1", "yes"):
        raise RuntimeError(
            "LANGCHAIN_TRACING_V2 must be set to true for tracing.\n"
            "Add LANGCHAIN_TRACING_V2=true to your .env file."
        )


def validate_smoke_llm(provider: SmokeProvider | None = None) -> None:
    """Ensure the selected smoke-test LLM provider is configured."""
    provider = provider or get_smoke_provider()

    if provider == "ollama":
        return  # local; no API key

    if provider == "groq":
        _require("GROQ_API_KEY")
        return

    if provider == "openai":
        _require("OPENAI_API_KEY")
        return

    _require("ANTHROPIC_API_KEY")


def validate_trace_smoke() -> None:
    """Validate all env vars needed for the LangSmith trace smoke test."""
    load_settings()
    validate_langsmith()
    validate_smoke_llm()

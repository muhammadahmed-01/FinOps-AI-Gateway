"""Environment configuration and validation."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

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


def validate_langsmith() -> None:
    """Ensure LangSmith tracing is configured."""
    _require("LANGCHAIN_API_KEY")
    tracing = os.getenv("LANGCHAIN_TRACING_V2", "").lower()
    if tracing not in ("true", "1", "yes"):
        raise RuntimeError(
            "LANGCHAIN_TRACING_V2 must be set to true for tracing.\n"
            "Add LANGCHAIN_TRACING_V2=true to your .env file."
        )


def validate_openai() -> None:
    """Ensure OpenAI is configured for smoke tests."""
    _require("OPENAI_API_KEY")


def validate_trace_smoke() -> None:
    """Validate all env vars needed for the LangSmith trace smoke test."""
    load_settings()
    validate_langsmith()
    validate_openai()

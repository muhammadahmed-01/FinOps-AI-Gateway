"""Tests for gateway configuration helpers."""

from __future__ import annotations

import pytest

from finops_gateway.config import anthropic_configured, routing_mode, validate_gateway


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("", False),
        ("sk-ant-...", False),
        ("sk-ant-api03-real-key-here", True),
    ],
)
def test_anthropic_configured(monkeypatch: pytest.MonkeyPatch, key: str, expected: bool) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    assert anthropic_configured() is expected


def test_routing_mode_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert routing_mode() == "demo"


def test_routing_mode_live(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-valid")
    assert routing_mode() == "live"


def test_validate_gateway_skips_anthropic_in_demo_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGCHAIN_API_KEY", "lsv2_test")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://finops:finops@localhost:5433/finops")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setenv("CLASSIFIER_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("finops_gateway.config.load_settings", lambda: None)

    validate_gateway()

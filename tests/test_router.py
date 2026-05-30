"""Tests for tier router helpers."""

from __future__ import annotations

import pytest

from finops_gateway.routing.router import _model_name_for_tier, _provider_for_tier


def test_provider_for_tier_simple_is_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert _provider_for_tier("simple") == "ollama"


def test_provider_for_tier_demo_uses_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert _provider_for_tier("medium") == "groq"
    assert _provider_for_tier("complex") == "groq"


def test_provider_for_tier_live_uses_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-valid")
    assert _provider_for_tier("medium") == "anthropic"


def test_model_name_defaults_match_pricing_tiers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROUTER_MEDIUM_MODEL", raising=False)
    monkeypatch.delenv("ROUTER_COMPLEX_MODEL", raising=False)
    assert _model_name_for_tier("medium") == "claude-haiku-4-5"
    assert _model_name_for_tier("complex") == "claude-sonnet-4-5"

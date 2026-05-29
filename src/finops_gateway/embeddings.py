"""Embedding model factory for ingestion and retrieval."""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.embeddings import Embeddings

EmbeddingProvider = Literal["ollama", "openai"]

_DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"


def get_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama").strip().lower()
    if provider not in ("ollama", "openai"):
        raise RuntimeError(
            f"Invalid EMBEDDING_PROVIDER: {provider!r}\n"
            "Use one of: ollama, openai"
        )
    return provider  # type: ignore[return-value]


def build_embeddings() -> Embeddings:
    provider = get_embedding_provider()

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=os.getenv("OLLAMA_EMBED_MODEL", _DEFAULT_OLLAMA_EMBED_MODEL),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    )

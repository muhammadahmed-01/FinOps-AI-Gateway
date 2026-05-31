"""Minimal crawler and chunker for LangGraph docs."""

from __future__ import annotations

import os
from collections import deque
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

LANGGRAPH_DOCS_SEEDS = [
    "https://docs.langchain.com/oss/python/langgraph/overview",
    "https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph",
    "https://docs.langchain.com/oss/python/langgraph/workflows-agents",
]

CUSTOM_DOCS_SEEDS = [
    "https://muhammadahmed-01.github.io/case-studies/concurrency-analysis/",
    "https://muhammadahmed-01.github.io/learnings/saa-blueprint/",
    "https://muhammadahmed-01.github.io/projects/infracost-sagemaker/",
]


def get_ingest_seeds() -> list[str]:
    seed_set = os.getenv("INGEST_SEED_SET", "langgraph").strip().lower()
    if seed_set == "custom":
        return CUSTOM_DOCS_SEEDS
    return LANGGRAPH_DOCS_SEEDS


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _is_langgraph_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc != "docs.langchain.com":
        return False
    return parsed.path.startswith("/oss/python/langgraph")


def _extract_text(soup: BeautifulSoup) -> tuple[str, str]:
    title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled"
    main = soup.find("main") or soup.find("article") or soup.find("body")
    if not main:
        return title, ""
    text = main.get_text(separator="\n", strip=True)
    return title, text


def crawl_langgraph_docs(max_pages: int = 25, timeout_s: float = 20.0) -> list[dict]:
    visited: set[str] = set()
    seeds = get_ingest_seeds()
    queue: deque[str] = deque(_normalize_url(url) for url in seeds)
    pages: list[dict] = []

    with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
        while queue and len(pages) < max_pages:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            try:
                response = client.get(current)
                response.raise_for_status()
            except Exception:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            title, text = _extract_text(soup)
            if text:
                pages.append({"url": str(response.url), "title": title, "text": text})

            for a_tag in soup.find_all("a", href=True):
                candidate = _normalize_url(urljoin(current, a_tag["href"]))
                if _is_langgraph_url(candidate) and candidate not in visited:
                    queue.append(candidate)

    return pages


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "900"))
    overlap = overlap or int(os.getenv("CHUNK_OVERLAP", "150"))
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(length, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = end - overlap

    return chunks

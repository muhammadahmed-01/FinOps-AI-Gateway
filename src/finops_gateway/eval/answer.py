"""Shared answer generation for RAG evaluation pipelines."""

from __future__ import annotations

import time

from langchain_core.messages import HumanMessage, SystemMessage

from finops_gateway.eval.ollama_llm import get_eval_answer_llm
from finops_gateway.llm_settings import llm_max_retries, llm_timeout_s
from finops_gateway.rag.db import RetrievedChunk

_EVAL_SYSTEM = (
    "Answer using only the provided context. If unsure, say you do not know. "
    "Be concise and factual."
)
_MAX_RATE_LIMIT_RETRIES = 5


def _build_eval_llm():
    import os

    provider = os.getenv("EVAL_LLM_PROVIDER", "ollama").strip().lower()
    timeout = llm_timeout_s()
    max_retries = llm_max_retries()

    if provider == "groq":
        from langchain_groq import ChatGroq

        model = os.getenv("EVAL_GROQ_MODEL", "llama-3.1-8b-instant")
        return ChatGroq(
            model=model,
            temperature=0,
            timeout=timeout,
            max_retries=max_retries,
        )

    return get_eval_answer_llm()


def answer_from_chunks(question: str, chunks: list[RetrievedChunk]) -> str:
    context = "\n\n".join(
        f"[{idx + 1}] {chunk.title}\n{chunk.content}"
        for idx, chunk in enumerate(chunks)
    )
    llm = _build_eval_llm()
    messages = [
        SystemMessage(content=_EVAL_SYSTEM),
        HumanMessage(
            content=(
                f"Question:\n<user_query>\n{question}\n</user_query>\n\n"
                f"Context:\n<context>\n{context}\n</context>"
            )
        ),
    ]

    for attempt in range(_MAX_RATE_LIMIT_RETRIES):
        try:
            response = llm.invoke(messages)
            content = response.content
            return content if isinstance(content, str) else str(content)
        except Exception as exc:
            if "rate_limit" not in str(exc).lower() or attempt == _MAX_RATE_LIMIT_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Unreachable")

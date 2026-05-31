"""Multi-turn chat using Redis session state + hybrid RAG."""

from __future__ import annotations

import os
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from finops_gateway.context import build_context_blocks
from finops_gateway.llm_settings import llm_max_retries, llm_timeout_s
from finops_gateway.rag.hybrid import hybrid_retrieve
from finops_gateway.routing.router import build_llm_for_tier
from finops_gateway.session.redis_store import SessionStore

_CHAT_SYSTEM = (
    "You are a helpful assistant using retrieved documentation and prior conversation. "
    "Use only the provided context for factual claims. "
    "Remember details the user shared earlier in the conversation."
)


def _build_chat_llm():
    tier = os.getenv("CHAT_TIER", "simple").strip().lower()
    if tier not in ("simple", "medium", "complex"):
        tier = "simple"
    return build_llm_for_tier(tier)  # type: ignore[arg-type]


def _format_history(store: SessionStore, session_id: str) -> str:
    messages = store.get_messages(session_id)
    if not messages:
        return ""
    lines = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def chat_turn(store: SessionStore, session_id: str, user_message: str, *, k: int = 4) -> str:
    retrieval = hybrid_retrieve(user_message, final_k=k)
    context_blocks = build_context_blocks(retrieval.chunks)
    history = _format_history(store, session_id)

    llm = _build_chat_llm()
    messages = [
        SystemMessage(content=_CHAT_SYSTEM),
        HumanMessage(
            content=(
                f"Conversation so far:\n<history>\n{history or '(none)'}\n</history>\n\n"
                f"User message:\n<user_query>\n{user_message}\n</user_query>\n\n"
                f"Retrieved context:\n<context>\n"
                f"{chr(10).join(context_blocks)}\n</context>"
            )
        ),
    ]
    response = llm.invoke(messages)
    content = response.content
    answer = content if isinstance(content, str) else str(content)

    store.append(session_id, "user", user_message)
    store.append(session_id, "assistant", answer)
    return answer


def verify_session_recall(store: SessionStore, session_id: str, needle: str) -> bool:
    transcript = _format_history(store, session_id).lower()
    return needle.lower() in transcript


def extract_name_from_answer(answer: str) -> str | None:
    match = re.search(r"\b(?:your name is|you(?:'|')?re|you are)\s+([A-Za-z][A-Za-z0-9_-]*)", answer, re.I)
    if match:
        return match.group(1)
    return None

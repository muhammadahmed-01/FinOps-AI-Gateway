"""Cost-aware model router by complexity tier."""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langsmith import traceable

from finops_gateway.routing.classifier import ComplexityResult, RoutingTier, classify_complexity
from finops_gateway.routing.pricing import estimate_cost_usd, extract_token_usage


@traceable(name="route_query")
def route_query(question: str) -> ComplexityResult:
    return classify_complexity(question)


def _anthropic_configured() -> bool:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key or key.startswith("sk-ant-..."):
        return False
    return key.startswith("sk-ant-")


def build_llm_for_tier(tier: RoutingTier) -> BaseChatModel:
    if tier == "simple":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("ROUTER_SIMPLE_MODEL", "qwen3:4b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )

    if not _anthropic_configured():
        # Demo mode: Groq answers (free tier); metrics use Claude list pricing above.
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0,
        )

    from langchain_anthropic import ChatAnthropic

    if tier == "medium":
        return ChatAnthropic(
            model=os.getenv("ROUTER_MEDIUM_MODEL", "claude-3-5-haiku-latest"),
            temperature=0,
        )

    return ChatAnthropic(
        model=os.getenv("ROUTER_COMPLEX_MODEL", "claude-sonnet-4-20250514"),
        temperature=0,
    )


@traceable(name="answer_with_router")
def answer_with_router(
    question: str,
    context_blocks: list[str],
    tier: RoutingTier,
) -> tuple[str, dict[str, int | float]]:
    llm = build_llm_for_tier(tier)
    context = "\n\n".join(context_blocks)
    prompt = (
        "Answer using only the provided context. If unsure, say you do not know.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer concisely and cite sources in plain text."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    usage = extract_token_usage(response)
    cost = estimate_cost_usd(tier, usage["input_tokens"], usage["output_tokens"])
    usage["cost_usd"] = cost
    return str(response.content), usage

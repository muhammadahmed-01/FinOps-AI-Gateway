"""Cost-aware model router by complexity tier."""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langsmith import traceable

from finops_gateway.config import anthropic_configured, routing_mode
from finops_gateway.llm_settings import llm_max_retries, llm_max_tokens, llm_timeout_s
from finops_gateway.routing.classifier import ComplexityResult, RoutingTier, classify_complexity
from finops_gateway.routing.pricing import estimate_cost_usd, extract_token_usage

_DEFAULT_MEDIUM_MODEL = "claude-haiku-4-5"
_DEFAULT_COMPLEX_MODEL = "claude-sonnet-4-5"
_DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"

_ANSWER_SYSTEM = (
    "Answer using only the provided context. If unsure, say you do not know. "
    "Answer concisely and cite sources in plain text."
)


@traceable(name="route_query", tags=["routing"])
def route_query(question: str) -> ComplexityResult:
    return classify_complexity(question)


def _model_name_for_tier(tier: RoutingTier) -> str:
    if tier == "simple":
        return os.getenv("ROUTER_SIMPLE_MODEL", "qwen3:4b")
    if tier == "medium":
        return os.getenv("ROUTER_MEDIUM_MODEL", _DEFAULT_MEDIUM_MODEL)
    return os.getenv("ROUTER_COMPLEX_MODEL", _DEFAULT_COMPLEX_MODEL)


def _provider_for_tier(tier: RoutingTier) -> str:
    if tier == "simple":
        return "ollama"
    if anthropic_configured():
        return "anthropic"
    return "groq"


def build_llm_for_tier(tier: RoutingTier) -> BaseChatModel:
    timeout = llm_timeout_s()
    max_retries = llm_max_retries()

    if tier == "simple":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("ROUTER_SIMPLE_MODEL", "qwen3:4b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
            timeout=timeout,
            num_retries=max_retries,
        )

    if not anthropic_configured():
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", _DEFAULT_GROQ_MODEL),
            temperature=0,
            timeout=timeout,
            max_retries=max_retries,
        )

    from langchain_anthropic import ChatAnthropic

    if tier == "medium":
        return ChatAnthropic(
            model=os.getenv("ROUTER_MEDIUM_MODEL", _DEFAULT_MEDIUM_MODEL),
            temperature=0,
            max_tokens=llm_max_tokens(),
            timeout=timeout,
            max_retries=max_retries,
        )

    return ChatAnthropic(
        model=os.getenv("ROUTER_COMPLEX_MODEL", _DEFAULT_COMPLEX_MODEL),
        temperature=0,
        max_tokens=llm_max_tokens(),
        timeout=timeout,
        max_retries=max_retries,
    )


def _message_content(response: AIMessage) -> str:
    content = response.content
    if isinstance(content, str):
        return content
    return str(content)


@traceable(name="answer_with_router", tags=["routing", "generation"])
def answer_with_router(
    question: str,
    context_blocks: list[str],
    tier: RoutingTier,
) -> tuple[str, dict[str, int | float | str]]:
    llm = build_llm_for_tier(tier)
    model_name = _model_name_for_tier(tier)
    provider = _provider_for_tier(tier)
    context = "\n\n".join(context_blocks)

    messages = [
        SystemMessage(content=_ANSWER_SYSTEM),
        HumanMessage(
            content=(
                f"Question:\n<user_query>\n{question}\n</user_query>\n\n"
                f"Context:\n<context>\n{context}\n</context>"
            )
        ),
    ]
    response = llm.invoke(messages)
    usage = extract_token_usage(response)
    cost = estimate_cost_usd(tier, usage["input_tokens"], usage["output_tokens"])
    usage["cost_usd"] = cost
    usage["ls_provider"] = provider
    usage["ls_model_name"] = model_name
    usage["routing_mode"] = routing_mode()
    return _message_content(response), usage

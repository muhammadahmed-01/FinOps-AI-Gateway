"""Query complexity classifier with structured LLM output."""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
from pydantic import BaseModel, Field

from finops_gateway.llm_settings import llm_max_retries, llm_timeout_s

RoutingTier = Literal["simple", "medium", "complex"]


class ComplexityResult(BaseModel):
    tier: RoutingTier = Field(description="Routing tier for the query")
    complexity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="0=simple factual lookup, 1=multi-step reasoning",
    )
    reasoning: str = Field(description="Brief explanation of the classification")
    needs_human_review: bool = Field(
        default=False,
        description="True when classification failed or confidence is low",
    )


_CLASSIFIER_SYSTEM = (
    "Classify user queries for an AI gateway router.\n"
    "- simple: single fact lookup, definitions, yes/no, one concept\n"
    "- medium: comparison, short explanation, moderate context synthesis\n"
    "- complex: multi-step reasoning, architecture design, debugging chains"
)


def _build_classifier_llm():
    provider = os.getenv("CLASSIFIER_PROVIDER", "groq").strip().lower()
    timeout = llm_timeout_s()
    max_retries = llm_max_retries()

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("CLASSIFIER_MODEL", "llama-3.1-8b-instant"),
            temperature=0,
            timeout=timeout,
            max_retries=max_retries,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("CLASSIFIER_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
            timeout=timeout,
            num_retries=max_retries,
        )
    raise RuntimeError(f"Unsupported CLASSIFIER_PROVIDER: {provider}")


def _default_classification(reason: str) -> ComplexityResult:
    return ComplexityResult(
        tier="medium",
        complexity_score=0.5,
        reasoning=reason,
        needs_human_review=True,
    )


@traceable(name="classify_complexity", tags=["routing"])
def classify_complexity(question: str) -> ComplexityResult:
    llm = _build_classifier_llm().with_structured_output(ComplexityResult)
    messages = [
        SystemMessage(content=_CLASSIFIER_SYSTEM),
        HumanMessage(
            content=f"Classify this query:\n<user_query>\n{question}\n</user_query>"
        ),
    ]
    try:
        result = llm.invoke(messages)
    except Exception as exc:
        return _default_classification(
            f"Classifier failed ({exc}); defaulting to medium tier."
        )

    if isinstance(result, ComplexityResult):
        return result
    try:
        return ComplexityResult.model_validate(result)
    except Exception as exc:
        return _default_classification(
            f"Classifier output invalid ({exc}); defaulting to medium tier."
        )

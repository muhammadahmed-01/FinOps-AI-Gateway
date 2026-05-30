"""Query complexity classifier with structured LLM output."""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.messages import HumanMessage
from langsmith import traceable
from pydantic import BaseModel, Field

RoutingTier = Literal["simple", "medium", "complex"]


class ComplexityResult(BaseModel):
    tier: RoutingTier = Field(description="Routing tier for the query")
    complexity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="0=simple factual lookup, 1=multi-step reasoning",
    )
    reasoning: str = Field(description="Brief explanation of the classification")


def _build_classifier_llm():
    provider = os.getenv("CLASSIFIER_PROVIDER", "groq").strip().lower()
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("CLASSIFIER_MODEL", "llama-3.1-8b-instant"),
            temperature=0,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("CLASSIFIER_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )
    raise RuntimeError(f"Unsupported CLASSIFIER_PROVIDER: {provider}")


@traceable(name="classify_complexity")
def classify_complexity(question: str) -> ComplexityResult:
    llm = _build_classifier_llm().with_structured_output(ComplexityResult)
    prompt = (
        "Classify this user query for an AI gateway router.\n"
        "- simple: single fact lookup, definitions, yes/no, one concept\n"
        "- medium: comparison, short explanation, moderate context synthesis\n"
        "- complex: multi-step reasoning, architecture design, debugging chains\n\n"
        f"Query: {question}"
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    if isinstance(result, ComplexityResult):
        return result
    return ComplexityResult.model_validate(result)

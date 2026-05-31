"""Generate Q&A evaluation pairs from ingested LangGraph doc chunks."""

from __future__ import annotations

import os
import random
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from finops_gateway.eval.dataset import DEFAULT_DATASET_PATH, EvalDataset, EvalPair
from finops_gateway.llm_settings import llm_max_retries, llm_timeout_s
from finops_gateway.rag.db import ChunkRecord, get_connection

_GENERATOR_SYSTEM = (
    "Create one evaluation question and a concise ground-truth answer "
    "strictly from the provided documentation excerpt. "
    "The question should be specific and answerable from the excerpt alone."
)


class GeneratedPair(BaseModel):
    question: str = Field(description="Evaluation question")
    ground_truth: str = Field(description="Reference answer grounded in the excerpt")


def _build_generator_llm():
    provider = os.getenv("EVAL_LLM_PROVIDER", "ollama").strip().lower()
    timeout = llm_timeout_s()
    max_retries = llm_max_retries()

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0.2,
            timeout=timeout,
            max_retries=max_retries,
        ).with_structured_output(GeneratedPair)

    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=os.getenv("EVAL_LLM_MODEL", "qwen3:4b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.2,
        timeout=timeout,
        num_retries=max_retries,
    ).with_structured_output(GeneratedPair)


def _pick_chunks(count: int, seed: int) -> list[ChunkRecord]:
    with get_connection() as conn:
        corpus = ChunkRecord.fetch_all(conn)
    if not corpus:
        raise RuntimeError("No chunks in database. Run finops-ingest-langgraph first.")

    rng = random.Random(seed)
    if len(corpus) <= count:
        return corpus
    return rng.sample(corpus, count)


def generate_eval_dataset(
    *,
    count: int = 50,
    seed: int = 42,
    output_path: Literal["default"] | None = "default",
) -> EvalDataset:
    llm = _build_generator_llm()
    chunks = _pick_chunks(count, seed)
    pairs: list[EvalPair] = []

    for idx, chunk in enumerate(chunks, start=1):
        messages = [
            SystemMessage(content=_GENERATOR_SYSTEM),
            HumanMessage(
                content=(
                    f"Title: {chunk.title}\n"
                    f"URL: {chunk.url}\n\n"
                    f"Excerpt:\n<context>\n{chunk.content[:2000]}\n</context>"
                )
            ),
        ]
        try:
            generated = llm.invoke(messages)
            if isinstance(generated, GeneratedPair):
                pair = generated
            else:
                pair = GeneratedPair.model_validate(generated)
        except Exception as exc:
            pair = GeneratedPair(
                question=f"What does the documentation say about {chunk.title}?",
                ground_truth=chunk.content[:300],
            )
            # Keep going — one failure should not abort the full dataset.
            _ = exc

        pairs.append(
            EvalPair(
                id=idx,
                question=pair.question.strip(),
                ground_truth=pair.ground_truth.strip(),
                source_url=chunk.url,
                source_title=chunk.title,
            )
        )

    dataset = EvalDataset(source="langgraph-docs", pairs=pairs)
    if output_path == "default":
        dataset.save(DEFAULT_DATASET_PATH)
    return dataset

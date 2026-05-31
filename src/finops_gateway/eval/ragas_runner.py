"""RAGAS evaluation runner comparing baseline vs hybrid retrieval."""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from typing import Any

from datasets import Dataset

from finops_gateway.embeddings import build_embeddings
from finops_gateway.eval.answer import answer_from_chunks
from finops_gateway.eval.dataset import EvalDataset
from finops_gateway.eval.metrics_proxy import embedding_answer_relevancy
from finops_gateway.eval.pipeline_cache import load_pipeline_cache, save_pipeline_cache
from finops_gateway.eval.ragas_compat import (
    RAGAS_LLM_METRICS,
    LangchainEmbeddingsWrapper,
    LangchainLLMWrapper,
    ragas_evaluate,
)
from finops_gateway.llm_settings import llm_max_retries, llm_max_tokens, ragas_timeout_s
from finops_gateway.metrics import record_ragas_scores
from finops_gateway.rag.baseline import baseline_retrieve
from finops_gateway.rag.hybrid import hybrid_retrieve
from ragas.run_config import RunConfig


@dataclass
class PipelineScores:
    pipeline: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    sample_count: int


def resolve_ragas_provider() -> str:
    """Prefer explicit env; else free Gemini if keyed; else local Ollama."""
    explicit = os.getenv("RAGAS_LLM_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    if os.getenv("GOOGLE_API_KEY", "").strip():
        return "gemini"
    return "ollama"


def _build_ragas_llm() -> LangchainLLMWrapper:
    provider = resolve_ragas_provider()
    timeout = ragas_timeout_s()
    max_retries = llm_max_retries()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=os.getenv("RAGAS_MODEL", "gpt-4o-mini"),
            temperature=0,
            timeout=timeout,
            max_retries=max_retries,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(
            model=os.getenv("RAGAS_MODEL", "claude-haiku-4-5"),
            temperature=0,
            max_tokens=llm_max_tokens(),
            timeout=timeout,
            max_retries=max_retries,
        )
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=os.getenv("RAGAS_MODEL", "gemini-2.0-flash"),
            temperature=0,
            timeout=timeout,
            max_retries=max_retries,
        )
    elif provider == "ollama":
        from finops_gateway.eval.llm_sanitize import wrap_sanitized
        from finops_gateway.eval.ollama_llm import get_ragas_judge_llm

        llm = wrap_sanitized(get_ragas_judge_llm())
    else:
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model=os.getenv("RAGAS_GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0,
            timeout=timeout,
            max_retries=max_retries,
        )

    return LangchainLLMWrapper(llm)


def _build_ragas_embeddings() -> LangchainEmbeddingsWrapper:
    return LangchainEmbeddingsWrapper(build_embeddings())


def _run_pipeline(
    dataset: EvalDataset,
    *,
    pipeline: str,
    k: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    embedder = build_embeddings()
    total = len(dataset.pairs)
    for idx, pair in enumerate(dataset.pairs, start=1):
        row_start = time.perf_counter()
        if pipeline == "baseline":
            retrieval = baseline_retrieve(pair.question, k=k)
        else:
            retrieval = hybrid_retrieve(pair.question, final_k=k)

        contexts = [chunk.content for chunk in retrieval.chunks]
        answer = answer_from_chunks(pair.question, retrieval.chunks)
        rows.append(
            {
                "question": pair.question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": pair.ground_truth,
                "answer_relevancy": embedding_answer_relevancy(
                    pair.question, answer, embedder
                ),
            }
        )
        snippet = pair.question[:70] + ("..." if len(pair.question) > 70 else "")
        print(
            f"  [{pipeline}] {idx}/{total} in {time.perf_counter() - row_start:.1f}s — {snippet}",
            flush=True,
        )
    return rows


def _score_rows(
    rows: list[dict[str, Any]],
    llm: LangchainLLMWrapper,
    embeddings: LangchainEmbeddingsWrapper,
) -> dict[str, float]:
    ragas_rows = [
        {
            "question": row["question"],
            "answer": row["answer"],
            "contexts": row["contexts"],
            "ground_truth": row["ground_truth"],
        }
        for row in rows
    ]
    timeout = int(ragas_timeout_s())
    provider = resolve_ragas_provider()
    fail_fast = os.getenv("RAGAS_FAIL_FAST", "true").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    raise_on_error = fail_fast and provider in {"groq", "gemini", "openai"}
    print(
        f"RAGAS scoring {len(rows)} rows (timeout={timeout}s/job, "
        f"max_workers={os.getenv('RAGAS_MAX_WORKERS', '1')}, "
        f"fail_fast={raise_on_error})...",
        flush=True,
    )
    score_start = time.perf_counter()
    eval_dataset = Dataset.from_list(ragas_rows)
    result = ragas_evaluate(
        dataset=eval_dataset,
        metrics=RAGAS_LLM_METRICS,
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=raise_on_error,
        run_config=RunConfig(
            timeout=timeout,
            max_workers=int(os.getenv("RAGAS_MAX_WORKERS", "1")),
        ),
    )
    print(f"RAGAS scoring finished in {time.perf_counter() - score_start:.1f}s.", flush=True)
    df = result.to_pandas()
    scores: dict[str, float] = {}
    for metric in ("faithfulness", "context_precision"):
        value = float(df[metric].mean(skipna=True))
        scores[metric] = value if not math.isnan(value) else 0.0
    scores["answer_relevancy"] = sum(row["answer_relevancy"] for row in rows) / len(rows)
    return scores


def run_ragas_comparison(
    dataset: EvalDataset,
    *,
    k: int = 4,
    push_metrics: bool = True,
    use_cache: bool = False,
    save_cache: bool = False,
) -> tuple[PipelineScores, PipelineScores]:
    llm = _build_ragas_llm()
    embeddings = _build_ragas_embeddings()

    if use_cache:
        cached = load_pipeline_cache()
        if cached and len(cached["baseline"]) == len(dataset.pairs):
            print("Using cached pipeline rows (skip retrieve+answer).", flush=True)
            baseline_rows = cached["baseline"]
            hybrid_rows = cached["hybrid"]
        else:
            print("Cache miss — running full pipeline.", flush=True)
            use_cache = False

    if not use_cache:
        from finops_gateway.eval.ollama_llm import warmup_ollama

        if os.getenv("EVAL_LLM_PROVIDER", "ollama").strip().lower() == "ollama":
            warmup_ollama()

        baseline_rows = _run_pipeline(dataset, pipeline="baseline", k=k)
        print(
            f"Baseline pipeline done ({len(baseline_rows)} rows). Scoring with RAGAS...",
            flush=True,
        )
        hybrid_rows = _run_pipeline(dataset, pipeline="hybrid", k=k)
        print(
            f"Hybrid pipeline done ({len(hybrid_rows)} rows). Scoring with RAGAS...",
            flush=True,
        )
        if save_cache:
            path = save_pipeline_cache(baseline_rows, hybrid_rows)
            print(f"Pipeline cache saved to {path}", flush=True)
    else:
        print("Scoring cached rows with RAGAS...", flush=True)

    baseline_scores = _score_rows(baseline_rows, llm, embeddings)
    print(
        f"Baseline scores: faithfulness={baseline_scores['faithfulness']:.4f} "
        f"context_precision={baseline_scores['context_precision']:.4f}",
        flush=True,
    )

    hybrid_scores = _score_rows(hybrid_rows, llm, embeddings)
    print(
        f"Hybrid scores: faithfulness={hybrid_scores['faithfulness']:.4f} "
        f"context_precision={hybrid_scores['context_precision']:.4f}",
        flush=True,
    )

    baseline = PipelineScores(
        pipeline="baseline",
        sample_count=len(baseline_rows),
        **baseline_scores,
    )
    hybrid = PipelineScores(
        pipeline="hybrid",
        sample_count=len(hybrid_rows),
        **hybrid_scores,
    )

    if push_metrics:
        record_ragas_scores("baseline", baseline_scores)
        record_ragas_scores("hybrid", hybrid_scores)

    return baseline, hybrid


def format_comparison_table(
    baseline: PipelineScores, hybrid: PipelineScores
) -> str:
    lines = [
        "| Metric | Baseline (cosine) | Hybrid+rerank | Delta |",
        "|--------|-------------------|---------------|-------|",
    ]
    for metric in ("faithfulness", "answer_relevancy", "context_precision"):
        b = getattr(baseline, metric)
        h = getattr(hybrid, metric)
        delta = h - b
        sign = "+" if delta >= 0 else ""
        lines.append(f"| {metric} | {b:.4f} | {h:.4f} | {sign}{delta:.4f} |")
    lines.append("")
    lines.append(
        "_answer_relevancy = embedding cosine proxy. "
        "RAGAS LLM judge metrics require a cloud judge with sufficient quota._"
    )
    return "\n".join(lines)

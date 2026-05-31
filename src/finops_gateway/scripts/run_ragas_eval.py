"""Run RAGAS evaluation: baseline cosine vs hybrid+rerank."""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

from finops_gateway.config import load_settings, validate_database, validate_embeddings
from finops_gateway.llm_settings import eval_llm_timeout_s, ragas_timeout_s
from finops_gateway.eval.dataset import EvalDataset
from finops_gateway.eval.ragas_runner import (
    format_comparison_table,
    resolve_ragas_provider,
    run_ragas_comparison,
)

DEFAULT_LOG = Path(__file__).resolve().parents[3] / "data" / "eval" / "ragas_run.log"


class _Tee:
    def __init__(self, stream, log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = stream
        self._file = log_path.open("w", encoding="utf-8", buffering=1)

    def write(self, text: str) -> int:
        self._stream.write(text)
        self._file.write(text)
        return len(text)

    def flush(self) -> None:
        self._stream.flush()
        if not self._file.closed:
            self._file.flush()

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare baseline vs hybrid RAG with RAGAS.")
    parser.add_argument("--k", type=int, default=4, help="Top-k chunks per pipeline.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Evaluate only first N pairs (0 = all).",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Skip pushing RAGAS scores to Pushgateway.",
    )
    parser.add_argument(
        "--log-file",
        default="",
        help="Write all output to this log file (line-buffered).",
    )
    parser.add_argument(
        "--save-cache",
        action="store_true",
        help="Save retrieve+answer rows to data/eval/pipeline_cache.json.",
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Skip retrieve+answer if pipeline_cache.json matches pair count.",
    )
    return parser.parse_args()


def _log(msg: str) -> None:
    print(msg, flush=True)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    log_path = Path(args.log_file) if args.log_file else DEFAULT_LOG
    tee = _Tee(sys.stdout, log_path)
    sys.stdout = tee  # type: ignore[assignment]

    try:
        load_settings()
        validate_database()
        validate_embeddings()

        dataset = EvalDataset.load()
        if args.limit > 0:
            dataset.pairs = dataset.pairs[: args.limit]

        _log(f"Log file: {log_path}")
        judge = resolve_ragas_provider()
        judge_detail = os.getenv("RAGAS_OLLAMA_MODEL", "llama3.2:1b") if judge == "ollama" else os.getenv("RAGAS_MODEL", "gemini-2.0-flash")
        _log(
            f"RAGAS judge: {judge} ({judge_detail}) | "
            f"Eval answers: {os.getenv('EVAL_LLM_PROVIDER', 'ollama')} "
            f"({os.getenv('EVAL_LLM_MODEL', 'qwen3:4b')})"
        )
        _log(f"Evaluating {len(dataset.pairs)} Q&A pairs (k={args.k})...")
        _log(
            f"Timeouts: eval_llm={eval_llm_timeout_s():.0f}s, ragas_job={ragas_timeout_s():.0f}s"
        )
        _log(
            f"Ollama: ctx={os.getenv('OLLAMA_NUM_CTX', '3072')} "
            f"eval_predict={os.getenv('EVAL_NUM_PREDICT', '256')} "
            f"judge_predict={os.getenv('RAGAS_NUM_PREDICT', '128')}\n"
        )

        baseline, hybrid = run_ragas_comparison(
            dataset,
            k=args.k,
            push_metrics=not args.no_push,
            use_cache=args.use_cache,
            save_cache=args.save_cache,
        )

        table = format_comparison_table(baseline, hybrid)
        _log(table)
        _log("")

        results_path = Path(__file__).resolve().parents[3] / "data" / "eval" / "ragas_results.md"
        results_path.parent.mkdir(parents=True, exist_ok=True)
        results_path.write_text(
            f"# RAGAS results ({len(dataset.pairs)} pairs, k={args.k})\n\n{table}\n",
            encoding="utf-8",
        )
        _log(f"Saved table to {results_path}")

        if (
            math.isnan(hybrid.context_precision)
            or math.isnan(baseline.context_precision)
            or hybrid.context_precision <= baseline.context_precision
        ):
            _log(
                "WARNING: hybrid context_precision did not beat baseline. "
                "Try smaller CHUNK_SIZE / CHUNK_OVERLAP and re-ingest LangGraph docs."
            )
        else:
            _log("OK: hybrid context_precision > baseline")

        if not args.no_push:
            _log("\nRAGAS scores pushed to Pushgateway — refresh Grafana panel: RAGAS Scores")
    finally:
        sys.stdout = tee._stream  # type: ignore[assignment]
        tee.close()


if __name__ == "__main__":
    main()

"""Shared, performance-tuned Ollama clients for eval (reuse + GPU-friendly settings)."""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel

_ANSWER_LLM: BaseChatModel | None = None
_JUDGE_LLM: BaseChatModel | None = None


def build_ollama_llm(
    *,
    model: str,
    num_predict: int,
    json_format: bool = False,
) -> BaseChatModel:
    from langchain_ollama import ChatOllama

    from finops_gateway.llm_settings import eval_llm_timeout_s, llm_max_retries

    kwargs: dict = {
        "model": model,
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "temperature": 0,
        "timeout": eval_llm_timeout_s(),
        "num_retries": llm_max_retries(),
        "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "3072")),
        "num_predict": num_predict,
        "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "30m"),
        # qwen3 thinking tags break RAGAS JSON parsers
        "reasoning": False,
    }
    if json_format:
        kwargs["format"] = "json"
    return ChatOllama(**kwargs)


def get_eval_answer_llm() -> BaseChatModel:
    global _ANSWER_LLM
    if _ANSWER_LLM is None:
        _ANSWER_LLM = build_ollama_llm(
            model=os.getenv("EVAL_LLM_MODEL", "qwen3:4b"),
            num_predict=int(os.getenv("EVAL_NUM_PREDICT", "256")),
        )
    return _ANSWER_LLM


def get_ragas_judge_llm() -> BaseChatModel:
    """RAGAS judge — JSON format + no thinking (qwen3 breaks parsers otherwise)."""
    global _JUDGE_LLM
    if _JUDGE_LLM is None:
        judge_model = os.getenv(
            "RAGAS_OLLAMA_MODEL",
            os.getenv("RAGAS_MODEL", "llama3.2:1b"),
        )
        use_json = os.getenv("RAGAS_OLLAMA_JSON", "false").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        eval_model = os.getenv("EVAL_LLM_MODEL", "qwen3:4b")
        if (
            not use_json
            and judge_model == eval_model
        ):
            _JUDGE_LLM = get_eval_answer_llm()
        else:
            _JUDGE_LLM = build_ollama_llm(
                model=judge_model,
                num_predict=int(os.getenv("RAGAS_NUM_PREDICT", "512")),
                json_format=use_json,
            )
    return _JUDGE_LLM


def warmup_ollama() -> None:
    """Load models into VRAM once before batch eval."""
    from langchain_core.messages import HumanMessage

    print("Warming up Ollama eval models...", flush=True)
    get_eval_answer_llm().invoke([HumanMessage(content="Reply OK.")])
    judge_model = os.getenv(
        "RAGAS_OLLAMA_MODEL", os.getenv("RAGAS_MODEL", "llama3.2:1b")
    )
    if os.getenv("RAGAS_LLM_PROVIDER", "ollama").strip().lower() == "ollama":
        get_ragas_judge_llm().invoke([HumanMessage(content='Reply with {"ok": true}.')])  # noqa: E501
    print("Ollama warmup done.", flush=True)

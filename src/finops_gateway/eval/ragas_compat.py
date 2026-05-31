"""Import ragas metrics used for evaluation."""

from __future__ import annotations

import sys
import types


def _patch_vertexai_import() -> None:
    module_name = "langchain_community.chat_models.vertexai"
    if module_name in sys.modules:
        return
    try:
        from langchain_google_vertexai import ChatVertexAI  # type: ignore import-untyped
    except ImportError:
        stub = types.ModuleType(module_name)

        class ChatVertexAI:  # noqa: D101
            pass

        stub.ChatVertexAI = ChatVertexAI
        sys.modules[module_name] = stub
        return

    module = types.ModuleType(module_name)
    module.ChatVertexAI = ChatVertexAI
    sys.modules[module_name] = module


_patch_vertexai_import()

from ragas import evaluate as ragas_evaluate  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.metrics import context_precision, faithfulness  # noqa: E402

# Groq rejects n>1 required by ragas answer_relevancy; use embedding proxy instead.
RAGAS_LLM_METRICS = [faithfulness, context_precision]

__all__ = [
    "RAGAS_LLM_METRICS",
    "LangchainEmbeddingsWrapper",
    "LangchainLLMWrapper",
    "context_precision",
    "faithfulness",
    "ragas_evaluate",
]

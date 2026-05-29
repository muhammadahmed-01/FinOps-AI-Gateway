"""Minimal LangSmith trace smoke test (provider selectable via .env)."""

from __future__ import annotations

import os

from langchain_core.messages import HumanMessage

from finops_gateway.config import validate_trace_smoke
from finops_gateway.llm import build_smoke_llm, get_smoke_provider


def main() -> None:
    validate_trace_smoke()

    provider = get_smoke_provider()
    llm = build_smoke_llm()
    response = llm.invoke(
        [HumanMessage(content="What is LangGraph in one sentence?")]
    )

    print(response.content)
    project = os.getenv("LANGCHAIN_PROJECT", "default")
    print(f"\nProvider: {provider}")
    print(f"Trace project: {project}")
    print(
        "Open LangSmith → Projects → "
        f"{project} to verify latency, tokens, and cost."
    )
    if provider == "ollama":
        print(
            "\nNote: Local Ollama runs show $0 cost in LangSmith; "
            "latency and token counts still appear."
        )


if __name__ == "__main__":
    main()

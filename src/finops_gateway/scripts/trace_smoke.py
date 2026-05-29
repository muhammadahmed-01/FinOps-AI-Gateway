"""Minimal LangSmith trace smoke test using OpenAI."""

from __future__ import annotations

import os

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from finops_gateway.config import validate_trace_smoke


def main() -> None:
    validate_trace_smoke()

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke(
        [HumanMessage(content="What is LangGraph in one sentence?")]
    )

    print(response.content)
    project = os.getenv("LANGCHAIN_PROJECT", "default")
    print(f"\nTrace project: {project}")
    print(
        "Open LangSmith → Projects → "
        f"{project} to verify latency, tokens, and cost."
    )


if __name__ == "__main__":
    main()

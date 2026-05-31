"""Clean local LLM output before RAGAS pydantic parsers run."""

from __future__ import annotations

import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


def sanitize_ragas_llm_output(text: str) -> str:
    """Strip thinking tags, markdown fences, and isolate JSON for RAGAS."""
    cleaned = text.strip()
    cleaned = re.sub(
        r"<\s*redacted_thinking\s*>.*?<\s*/\s*redacted_thinking\s*>",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    cleaned = re.sub(
        r"<\s*think\s*>.*?<\s*/\s*think\s*>",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    for pattern in (r"(\{.*\})", r"(\[.*\])"):
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            return match.group(1).strip()
    return cleaned


def _sanitize_message(message: BaseMessage) -> BaseMessage:
    if not isinstance(message, AIMessage):
        return message
    content = message.content
    if isinstance(content, str):
        return AIMessage(content=sanitize_ragas_llm_output(content), id=message.id)
    if isinstance(content, list):
        parts: list[Any] = []
        for block in content:
            if isinstance(block, str):
                parts.append(sanitize_ragas_llm_output(block))
            elif isinstance(block, dict) and block.get("type") == "text":
                text = str(block.get("text", ""))
                parts.append({**block, "text": sanitize_ragas_llm_output(text)})
            else:
                parts.append(block)
        return AIMessage(content=parts, id=message.id)
    return message


class SanitizingChatModel(BaseChatModel):
    """Wraps a chat model and sanitizes AIMessage content for RAGAS parsing."""

    llm: BaseChatModel

    @property
    def _llm_type(self) -> str:
        return f"sanitized-{self.llm._llm_type}"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        result = self.llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        generations: list[list[ChatGeneration]] = []
        for gen_list in result.generations:
            sanitized: list[ChatGeneration] = []
            for gen in gen_list:
                msg = _sanitize_message(gen.message)
                sanitized.append(
                    ChatGeneration(message=msg, generation_info=gen.generation_info)
                )
            generations.append(sanitized)
        return ChatResult(generations=generations, llm_output=result.llm_output)

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return self.llm._identifying_params


def wrap_sanitized(llm: BaseChatModel) -> BaseChatModel:
    return SanitizingChatModel(llm=llm)

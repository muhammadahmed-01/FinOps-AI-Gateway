"""Redis-backed multi-turn conversation session store."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

import redis

Role = Literal["user", "assistant"]


@dataclass
class SessionMessage:
    role: Role
    content: str
    timestamp: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionMessage:
        return cls(
            role=data["role"],  # type: ignore[arg-type]
            content=str(data["content"]),
            timestamp=str(data.get("timestamp", "")),
        )


def _session_key(session_id: str) -> str:
    return f"finops:session:{session_id}"


def get_redis_client() -> redis.Redis:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0").strip()
    return redis.from_url(url, decode_responses=True)


class SessionStore:
    def __init__(self, client: redis.Redis | None = None) -> None:
        self._client = client or get_redis_client()
        self._ttl_s = int(os.getenv("SESSION_TTL_S", str(24 * 3600)))

    def new_session_id(self) -> str:
        return uuid.uuid4().hex

    def append(self, session_id: str, role: Role, content: str) -> None:
        message = SessionMessage(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        key = _session_key(session_id)
        self._client.rpush(key, json.dumps(message.to_dict()))
        self._client.expire(key, self._ttl_s)

    def get_messages(self, session_id: str) -> list[SessionMessage]:
        key = _session_key(session_id)
        raw_items = self._client.lrange(key, 0, -1)
        return [SessionMessage.from_dict(json.loads(item)) for item in raw_items]

    def clear(self, session_id: str) -> None:
        self._client.delete(_session_key(session_id))

    def ping(self) -> bool:
        return bool(self._client.ping())

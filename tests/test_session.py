"""Tests for Redis session store."""

from __future__ import annotations

import json

from finops_gateway.session.redis_store import SessionStore


class FakeRedis:
    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = {}
        self.ttl: dict[str, int] = {}

    def rpush(self, key: str, value: str) -> None:
        self.lists.setdefault(key, []).append(value)

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        items = self.lists.get(key, [])
        if end == -1:
            end = len(items) - 1
        return items[start : end + 1]

    def expire(self, key: str, ttl: int) -> None:
        self.ttl[key] = ttl

    def delete(self, key: str) -> None:
        self.lists.pop(key, None)

    def ping(self) -> bool:
        return True


def test_session_append_and_read() -> None:
    store = SessionStore(client=FakeRedis())  # type: ignore[arg-type]
    session_id = store.new_session_id()
    store.append(session_id, "user", "Hello")
    store.append(session_id, "assistant", "Hi there")

    messages = store.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].content == "Hi there"


def test_session_clear() -> None:
    fake = FakeRedis()
    store = SessionStore(client=fake)  # type: ignore[arg-type]
    session_id = store.new_session_id()
    store.append(session_id, "user", "test")
    store.clear(session_id)
    assert store.get_messages(session_id) == []

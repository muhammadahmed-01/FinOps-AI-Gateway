"""Postgres + pgvector helpers for minimal RAG."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


@dataclass
class ChunkRecord:
    id: int
    url: str
    title: str
    chunk_index: int
    content: str

    @classmethod
    def fetch_all(cls, conn: psycopg.Connection[Any]) -> list["ChunkRecord"]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, url, title, chunk_index, content
                FROM doc_chunks
                ORDER BY id;
                """
            )
            rows = cur.fetchall()
        return [
            cls(
                id=row["id"],
                url=row["url"],
                title=row["title"],
                chunk_index=row["chunk_index"],
                content=row["content"],
            )
            for row in rows
        ]


@dataclass
class RetrievedChunk:
    id: int
    url: str
    title: str
    chunk_index: int
    content: str
    score: float


def get_connection() -> psycopg.Connection[Any]:
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set.")
    conn = psycopg.connect(dsn, row_factory=dict_row)
    register_vector(conn)
    return conn


def ensure_schema(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS doc_chunks (
                id BIGSERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    conn.commit()


def clear_source(conn: psycopg.Connection[Any], source: str) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM doc_chunks WHERE source = %s;", (source,))
    conn.commit()


def insert_chunk(
    conn: psycopg.Connection[Any],
    *,
    source: str,
    url: str,
    title: str,
    chunk_index: int,
    content: str,
    embedding: list[float],
    metadata: dict[str, Any],
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO doc_chunks
                (source, url, title, chunk_index, content, embedding, metadata)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s);
            """,
            (source, url, title, chunk_index, content, embedding, Jsonb(metadata)),
        )


def query_similar_chunks(
    conn: psycopg.Connection[Any], query_embedding: list[float], k: int
) -> list[RetrievedChunk]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                url,
                title,
                chunk_index,
                content,
                (1 - (embedding <=> %s::vector))::float8 AS score
            FROM doc_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, k),
        )
        rows = cur.fetchall()
    return [
        RetrievedChunk(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            score=float(row["score"]),
        )
        for row in rows
    ]

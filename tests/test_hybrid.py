"""Tests for RRF fusion in hybrid retrieval."""

from __future__ import annotations

from finops_gateway.rag.hybrid import _rrf_fuse


def test_rrf_fuse_prefers_items_in_both_rankings() -> None:
    rankings = [
        [1, 2, 3],
        [3, 1, 4],
    ]
    scores = _rrf_fuse(rankings, k=60)
    assert scores[1] > scores[2]
    assert scores[1] > scores[4]
    assert scores[3] > scores[2]


def test_rrf_fuse_single_ranking() -> None:
    scores = _rrf_fuse([[10, 20]], k=60)
    assert scores[10] > scores[20]

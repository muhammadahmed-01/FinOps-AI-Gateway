"""Cache retrieve+answer rows so RAGAS re-runs skip the slow pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CACHE_PATH = Path(__file__).resolve().parents[3] / "data" / "eval" / "pipeline_cache.json"


def load_pipeline_cache() -> dict[str, list[dict[str, Any]]] | None:
    if not _CACHE_PATH.exists():
        return None
    data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    return {"baseline": data["baseline"], "hybrid": data["hybrid"]}


def save_pipeline_cache(
    baseline: list[dict[str, Any]], hybrid: list[dict[str, Any]]
) -> Path:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps({"baseline": baseline, "hybrid": hybrid}, indent=2),
        encoding="utf-8",
    )
    return _CACHE_PATH

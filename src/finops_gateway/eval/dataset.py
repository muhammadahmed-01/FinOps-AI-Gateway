"""Evaluation dataset types and persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_PATH = _PROJECT_ROOT / "data" / "eval" / "langgraph_qa_50.json"


class EvalPair(BaseModel):
    id: int
    question: str
    ground_truth: str
    source_url: str = ""
    source_title: str = ""


class EvalDataset(BaseModel):
    version: int = 1
    source: str = "langgraph-docs"
    pairs: list[EvalPair] = Field(default_factory=list)

    def save(self, path: Path | None = None) -> Path:
        target = path or DEFAULT_DATASET_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: Path | None = None) -> EvalDataset:
        target = path or DEFAULT_DATASET_PATH
        if not target.exists():
            raise FileNotFoundError(
                f"Eval dataset not found at {target}. "
                "Run: uv run finops-generate-eval-dataset"
            )
        data = json.loads(target.read_text(encoding="utf-8"))
        return cls.model_validate(data)


def dataset_to_dict_rows(dataset: EvalDataset) -> list[dict[str, Any]]:
    return [pair.model_dump() for pair in dataset.pairs]

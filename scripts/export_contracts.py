from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.models import (
    ChunkMetadata,
    Citation,
    EvaluationAnnotation,
    EvaluationItem,
    KnowledgePoint,
    LearningEvent,
    TaskTemplate,
)
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_MODELS = [
    ChunkMetadata,
    KnowledgePoint,
    Citation,
    EvaluationItem,
    EvaluationAnnotation,
    TaskTemplate,
    LearningEvent,
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
    )


def export_contracts(destination: Path | None = None) -> Path:
    output = destination or ROOT / "contracts"
    _write_json(output / "openapi.json", create_app().openapi())
    for model in SCHEMA_MODELS:
        _write_json(
            output / "schemas" / f"{model.__name__}.json", model.model_json_schema()
        )
    return output


if __name__ == "__main__":
    result = export_contracts()
    print(f"Contracts exported to {result.relative_to(ROOT)}")

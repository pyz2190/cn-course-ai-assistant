from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.domain.models import (
    ChunkMetadata,
    Citation,
    EvaluationItem,
    KnowledgePoint,
    LearningEvent,
    TaskTemplate,
)
from app.main import create_app

SCHEMA_MODELS = [
    ChunkMetadata,
    KnowledgePoint,
    Citation,
    EvaluationItem,
    TaskTemplate,
    LearningEvent,
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
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

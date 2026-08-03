import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domain.models import EvaluationAnnotation, EvaluationItem

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ANNOTATION_EXAMPLE = PROJECT_ROOT / "contracts" / "examples" / "evaluation-annotation.json"
EVALUATION_DIRECTORY = PROJECT_ROOT / "evaluation"


def _load_annotation_example() -> dict[str, object]:
    return json.loads(ANNOTATION_EXAMPLE.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_evaluation_annotation_example_is_valid() -> None:
    annotation = EvaluationAnnotation.model_validate(_load_annotation_example())

    assert annotation.evaluation_id == "QA-PROTOCOL-001"
    assert annotation.expected_citations == []
    assert annotation.reviewer is None
    assert annotation.reviewed_at is None


def test_evaluation_annotation_requires_evaluation_id() -> None:
    data = _load_annotation_example()
    del data["evaluation_id"]

    with pytest.raises(ValidationError):
        EvaluationAnnotation.model_validate(data)


@pytest.mark.parametrize("key_points", [[], [""]])
def test_evaluation_annotation_rejects_empty_key_points(key_points: list[str]) -> None:
    data = _load_annotation_example()
    data["key_points"] = key_points

    with pytest.raises(ValidationError):
        EvaluationAnnotation.model_validate(data)


def test_evaluation_annotation_rejects_duplicate_key_points() -> None:
    data = _load_annotation_example()
    data["key_points"] = ["同一个关键点", "同一个关键点"]

    with pytest.raises(ValidationError):
        EvaluationAnnotation.model_validate(data)


def test_evaluation_annotation_rejects_invalid_review_status() -> None:
    data = _load_annotation_example()
    data["review_status"] = "passed"

    with pytest.raises(ValidationError):
        EvaluationAnnotation.model_validate(data)


@pytest.mark.parametrize(
    "citation",
    [
        {"resource_id": "resource-cn-textbook-001", "page_start": 0},
        {
            "resource_id": "resource-cn-textbook-001",
            "page_start": 2,
            "page_end": 1,
        },
    ],
)
def test_evaluation_annotation_rejects_invalid_citation_pages(
    citation: dict[str, object],
) -> None:
    data = _load_annotation_example()
    data["expected_citations"] = [citation]

    with pytest.raises(ValidationError):
        EvaluationAnnotation.model_validate(data)


@pytest.mark.parametrize(
    "review_status, reviewer, reviewed_at",
    [
        ("approved", None, "2026-08-03T00:00:00Z"),
        ("approved", "reviewer-a", None),
        ("rejected", None, "2026-08-03T00:00:00Z"),
    ],
)
def test_finalized_annotation_requires_reviewer_and_timestamp(
    review_status: str, reviewer: str | None, reviewed_at: str | None
) -> None:
    data = _load_annotation_example()
    data.update(
        {
            "review_status": review_status,
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
        }
    )

    with pytest.raises(ValidationError):
        EvaluationAnnotation.model_validate(data)


def test_evaluation_annotation_rejects_extra_fields() -> None:
    data = _load_annotation_example()
    data["unexpected"] = "value"

    with pytest.raises(ValidationError):
        EvaluationAnnotation.model_validate(data)


def test_evaluation_jsonl_is_valid_and_relationally_consistent() -> None:
    question_bank = _load_jsonl(EVALUATION_DIRECTORY / "question_bank.jsonl")
    annotations = _load_jsonl(EVALUATION_DIRECTORY / "annotations.jsonl")

    questions = [EvaluationItem.model_validate(item) for item in question_bank]
    validated_annotations = [EvaluationAnnotation.model_validate(item) for item in annotations]
    question_ids = [item.evaluation_id for item in questions]
    annotation_ids = [item.evaluation_id for item in validated_annotations]

    assert len(question_ids) == len(set(question_ids))
    assert len(annotation_ids) == len(set(annotation_ids))
    assert set(annotation_ids).issubset(question_ids)
    assert (EVALUATION_DIRECTORY / "evaluation_set.jsonl").read_text(encoding="utf-8") == ""

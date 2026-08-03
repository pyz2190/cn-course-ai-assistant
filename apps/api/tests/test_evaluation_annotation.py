import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.adapters.mock import MOCK_CHUNKS, MOCK_TASKS
from app.domain.models import EvaluationAnnotation, EvaluationItem

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ANNOTATION_EXAMPLE = PROJECT_ROOT / "contracts" / "examples" / "evaluation-annotation.json"
EVALUATION_DIRECTORY = PROJECT_ROOT / "evaluation"
EXPECTED_CATEGORIES = {
    "concept",
    "protocol_detail",
    "tool_tutorial",
    "lab",
    "common_error",
    "review",
}
EXPECTED_DIMENSIONS = {
    "correctness",
    "citation_accuracy",
    "hallucination_rate",
}
EXISTING_MOCK_KNOWLEDGE_POINT_IDS = {
    knowledge_point_id
    for item in [*MOCK_CHUNKS, *MOCK_TASKS]
    for knowledge_point_id in item.knowledge_point_ids
}


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


def test_pending_review_annotation_does_not_require_reviewer_metadata() -> None:
    data = _load_annotation_example()
    data.update(
        {
            "review_status": "pending_review",
            "reviewer": None,
            "reviewed_at": None,
        }
    )

    annotation = EvaluationAnnotation.model_validate(data)

    assert annotation.review_status.value == "pending_review"
    assert annotation.reviewer is None
    assert annotation.reviewed_at is None


def test_w2_evaluation_jsonl_is_valid_and_relationally_consistent() -> None:
    question_bank = _load_jsonl(EVALUATION_DIRECTORY / "question_bank.jsonl")
    annotations = _load_jsonl(EVALUATION_DIRECTORY / "annotations.jsonl")

    questions = [EvaluationItem.model_validate(item) for item in question_bank]
    validated_annotations = [EvaluationAnnotation.model_validate(item) for item in annotations]
    question_ids = [item.evaluation_id for item in questions]
    annotation_ids = [item.evaluation_id for item in validated_annotations]

    assert len(questions) >= 30
    assert len(validated_annotations) >= 30
    assert len(question_ids) == len(set(question_ids))
    assert len(annotation_ids) == len(set(annotation_ids))
    assert set(annotation_ids) == set(question_ids)
    assert {item.category.value for item in questions} == EXPECTED_CATEGORIES
    assert all(
        sum(question.category.value == category for question in questions) >= 5
        for category in EXPECTED_CATEGORIES
    )
    assert all(item.knowledge_point_ids for item in questions)
    assert {
        knowledge_point_id for item in questions for knowledge_point_id in item.knowledge_point_ids
    }.issubset(EXISTING_MOCK_KNOWLEDGE_POINT_IDS)
    assert all(
        len(item.scoring_dimensions) == len(EXPECTED_DIMENSIONS)
        and set(item.scoring_dimensions) == EXPECTED_DIMENSIONS
        for item in questions
    )
    assert all(item.key_points for item in validated_annotations)
    statuses = {item.review_status.value for item in validated_annotations}
    assert statuses == {"pending_review"}
    assert "approved" not in statuses
    assert all(
        item.reviewer is None and item.reviewed_at is None
        for item in validated_annotations
        if item.review_status.value == "pending_review"
    )
    assert all(item.expected_citations == [] for item in validated_annotations)
    assert (EVALUATION_DIRECTORY / "evaluation_set.jsonl").read_text(encoding="utf-8") == ""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domain.enums import (
    AccessLevel,
    ContentType,
    Difficulty,
    Language,
    ParseStatus,
    QuestionCategory,
    ScoringDimension,
)
from app.domain.models import AskRequest, ChunkMetadata, EvaluationItem

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVALUATION_ITEM_EXAMPLE = (
    PROJECT_ROOT / "contracts" / "examples" / "evaluation-item.json"
)


def _load_evaluation_item_example() -> dict[str, object]:
    return json.loads(EVALUATION_ITEM_EXAMPLE.read_text(encoding="utf-8"))


def test_chunk_rejects_reversed_page_range() -> None:
    with pytest.raises(ValidationError):
        ChunkMetadata(
            chunk_id="chunk-1",
            resource_id="resource-1",
            knowledge_point_ids=["kp-1"],
            title="TCP",
            content="content",
            chapter="运输层",
            page_start=5,
            page_end=4,
            language=Language.ZH,
            content_type=ContentType.PDF,
            version="1",
            access_level=AccessLevel.COURSE,
            parse_status=ParseStatus.PARSED,
            updated_at=datetime.now(UTC),
        )


def test_question_rejects_whitespace() -> None:
    with pytest.raises(ValidationError):
        AskRequest(course_id="course-1", user_id="user-1", question="   ")


def test_evaluation_item_example_is_valid_json_and_matches_contract() -> None:
    data = _load_evaluation_item_example()

    item = EvaluationItem.model_validate(data)

    assert item.evaluation_id == "QA-PROTOCOL-001"
    assert item.knowledge_point_ids == ["kp-transport-tcp-handshake"]
    assert set(item.scoring_dimensions) == set(ScoringDimension)


def test_evaluation_categories_and_scoring_dimensions_are_frozen() -> None:
    assert {category.value for category in QuestionCategory} == {
        "concept",
        "protocol_detail",
        "tool_tutorial",
        "lab",
        "common_error",
        "review",
    }
    assert {dimension.value for dimension in ScoringDimension} == {
        "correctness",
        "citation_accuracy",
        "hallucination_rate",
    }
    assert {difficulty.value for difficulty in Difficulty} == {
        "introductory",
        "intermediate",
        "advanced",
    }


@pytest.mark.parametrize(
    "invalid_category", ["protocol", "protocol-details", "tutorial", "experiment"]
)
def test_evaluation_item_rejects_invalid_categories(invalid_category: str) -> None:
    data = _load_evaluation_item_example()
    data["category"] = invalid_category

    with pytest.raises(ValidationError):
        EvaluationItem.model_validate(data)

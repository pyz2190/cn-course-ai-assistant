from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.enums import AccessLevel, ContentType, Language, ParseStatus
from app.domain.models import AskRequest, ChunkMetadata


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

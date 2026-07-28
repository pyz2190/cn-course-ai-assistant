from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)

from app.domain.enums import (
    AccessLevel,
    ContentType,
    Difficulty,
    EventType,
    Language,
    ParseStatus,
    QuestionCategory,
    ResourceType,
    ReviewStatus,
    ScoringDimension,
    SyncStatus,
    TaskStatus,
    TaskType,
)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ChunkMetadata(ContractModel):
    chunk_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    knowledge_point_ids: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    chapter: str = Field(min_length=1)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    language: Language
    content_type: ContentType
    source_url: str | None = None
    version: str = Field(min_length=1)
    access_level: AccessLevel
    parse_status: ParseStatus
    updated_at: datetime

    @model_validator(mode="after")
    def validate_page_range(self) -> "ChunkMetadata":
        if self.page_start is None and self.page_end is not None:
            raise ValueError("page_start is required when page_end is provided")
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be greater than or equal to page_start")
        return self


class KnowledgePoint(ContractModel):
    knowledge_point_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    chapter: str = Field(min_length=1)
    parent_id: str | None = None
    kind: str = Field(min_length=1)
    difficulty: Difficulty
    keywords_zh: list[str] = Field(default_factory=list)
    keywords_en: list[str] = Field(default_factory=list)
    prerequisite_ids: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)
    review_status: ReviewStatus
    maintainer: str = Field(min_length=1)


class Citation(ContractModel):
    citation_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    chapter: str = Field(min_length=1)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    quote: str = Field(min_length=1)
    source_url: str | None = None


class ResourceImportRequest(ContractModel):
    course_id: str = Field(min_length=1)
    resource_type: ResourceType
    title: str = Field(min_length=1)
    version: str = Field(min_length=1)
    language: Language
    content_type: ContentType
    source_url: str | None = None


class ResourceImportResponse(ContractModel):
    resource_id: str = Field(min_length=1)
    sync_status: SyncStatus
    metadata: ChunkMetadata | None = None
    error: str | None = None


class AskRequest(ContractModel):
    course_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must contain non-whitespace text")
        return value


class AskResponse(ContractModel):
    answer: str = Field(min_length=1)
    citations: list[Citation] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    request_id: str = Field(min_length=1)


class TaskTemplate(ContractModel):
    task_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    task_type: TaskType
    knowledge_point_ids: list[str] = Field(min_length=1)
    resource_ids: list[str] = Field(min_length=1)
    prerequisite_ids: list[str] = Field(default_factory=list)
    completion_criteria: list[str] = Field(min_length=1)
    ai_feedback_points: list[str] = Field(min_length=1)
    status: TaskStatus


class LearningEvent(ContractModel):
    event_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    event_type: EventType
    object_id: str = Field(min_length=1)
    occurred_at: datetime
    payload: dict[str, JsonValue] = Field(default_factory=dict)


class EvaluationItem(ContractModel):
    evaluation_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_answer: str = Field(min_length=1)
    category: QuestionCategory
    difficulty: Difficulty
    knowledge_point_ids: list[str] = Field(min_length=1)
    scoring_dimensions: list[ScoringDimension] = Field(min_length=1)


class ApiError(ContractModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    details: dict[str, JsonValue] | None = None


class HealthResponse(ContractModel):
    status: str
    service: str
    mode: str

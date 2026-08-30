from datetime import datetime
from typing import Literal

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
    EvaluationReviewStatus,
    EventType,
    ExerciseSource,
    ExerciseType,
    FeedbackStatus,
    KnowledgeBaseChangeStatus,
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
    extracted_content_type: ContentType | None = None
    source_url: str | None = None
    source_path: str | None = None
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
    retrieval_score: float | None = Field(default=None, ge=-1, le=1)
    rerank_score: float | None = None


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


class ResourceUploadResponse(ContractModel):
    resource_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    chunk_count: int = Field(ge=0)
    parse_status: ParseStatus
    chunks: list[ChunkMetadata] = Field(default_factory=list)
    indexed_chunks: int | None = Field(
        default=None,
        ge=0,
        description="向量库在本次导入后的 Chunk 总数；为空表示未执行向量化。",
    )
    error: str | None = None


class ResourceSummary(ContractModel):
    """已导入资料的概览，用于确认解析与入库结果。"""

    resource_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    chunk_count: int = Field(ge=1)
    language: Language
    content_type: ContentType
    version: str = Field(min_length=1)
    updated_at: datetime


class AskRequest(ContractModel):
    course_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=2000)
    knowledge_point_ids: list[str] = Field(default_factory=list)
    resource_ids: list[str] = Field(default_factory=list)
    task_id: str | None = Field(default=None, min_length=1)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must contain non-whitespace text")
        return value


class AskResponse(ContractModel):
    answer: str = Field(min_length=1)
    citations: list[Citation]
    confidence: float = Field(ge=0, le=1)
    request_id: str = Field(min_length=1)
    degraded: bool = False
    mode: Literal["offline", "external"] = "offline"


class Exercise(ContractModel):
    """课程试题，是任务完成判据的可判定载体。

    试题通过 `knowledge_point_ids` 挂到知识图谱，通过 `resource_ids` 指回命题依据的
    课程资料，使「任务 → 知识点 → 资料 → 试题」形成闭合的引用链。
    """

    exercise_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    exercise_type: ExerciseType
    knowledge_point_ids: list[str] = Field(min_length=1)
    resource_ids: list[str] = Field(default_factory=list)
    difficulty: Difficulty
    options: list[str] = Field(
        default_factory=list,
        description="选择题选项；非选择题为空。",
    )
    reference_answer: str = Field(min_length=1)
    explanation: str = ""
    source: ExerciseSource
    review_status: ReviewStatus

    @model_validator(mode="after")
    def validate_options(self) -> "Exercise":
        choice_types = {ExerciseType.SINGLE_CHOICE, ExerciseType.MULTIPLE_CHOICE}
        if self.exercise_type in choice_types and len(self.options) < 2:
            raise ValueError("choice exercises require at least two options")
        if self.exercise_type not in choice_types and self.options:
            raise ValueError("options are only allowed for choice exercises")
        return self


class TaskTemplate(ContractModel):
    task_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    task_type: TaskType
    knowledge_point_ids: list[str] = Field(min_length=1)
    resource_ids: list[str] = Field(min_length=1)
    exercise_ids: list[str] = Field(
        default_factory=list,
        description="任务自测与验收所用的试题标识，对应 /exercises 接口。",
    )
    prerequisite_ids: list[str] = Field(default_factory=list)
    completion_criteria: list[str] = Field(min_length=1)
    ai_feedback_points: list[str] = Field(min_length=1)
    status: TaskStatus


class TaskPublishRequest(ContractModel):
    task_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    task_type: TaskType
    knowledge_point_ids: list[str] = Field(min_length=1)
    resource_ids: list[str] = Field(min_length=1)
    exercise_ids: list[str] = Field(
        default_factory=list,
        description="任务自测与验收所用的试题标识，对应 /exercises 接口。",
    )
    prerequisite_ids: list[str] = Field(default_factory=list)
    completion_criteria: list[str] = Field(min_length=1)
    ai_feedback_points: list[str] = Field(min_length=1)
    status: TaskStatus = Field(
        default=TaskStatus.PUBLISHED,
        description="发布状态；传 draft 可先存为草稿，稍后再发布。",
    )


class TaskStatusUpdateRequest(ContractModel):
    """任务状态流转请求，用于发布草稿或标记任务完成。"""

    status: TaskStatus


class AnswerFeedbackCreate(ContractModel):
    course_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    citation_ids: list[str] = Field(default_factory=list)


class AnswerFeedback(AnswerFeedbackCreate):
    feedback_id: str = Field(min_length=1)
    status: FeedbackStatus
    created_at: datetime
    reviewer: str | None = Field(default=None, min_length=1)
    reviewed_at: datetime | None = None
    review_notes: str = ""
    knowledge_base_change_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_review_state(self) -> "AnswerFeedback":
        if self.status == FeedbackStatus.PENDING_REVIEW:
            if self.reviewer is not None or self.reviewed_at is not None:
                raise ValueError("pending feedback must not contain review metadata")
            if self.knowledge_base_change_id is not None:
                raise ValueError("pending feedback must not reference a knowledge-base change")
            return self

        if self.reviewer is None or self.reviewed_at is None:
            raise ValueError("reviewer and reviewed_at are required after review")
        if self.status != FeedbackStatus.APPROVED and self.knowledge_base_change_id is not None:
            raise ValueError("only approved feedback may reference a knowledge-base change")
        return self


class FeedbackReviewRequest(ContractModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = Field(min_length=1)
    review_notes: str = ""
    suggested_action: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_suggested_action(self) -> "FeedbackReviewRequest":
        if self.decision == "approved" and self.suggested_action is None:
            raise ValueError("suggested_action is required when approving feedback")
        if self.decision == "rejected" and self.suggested_action is not None:
            raise ValueError("suggested_action is only allowed when approving feedback")
        return self


class KnowledgeBaseChangeTask(ContractModel):
    change_id: str = Field(min_length=1)
    feedback_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    suggested_action: str = Field(min_length=1)
    status: KnowledgeBaseChangeStatus
    created_at: datetime
    handler: str | None = None
    updated_at: datetime | None = None
    resolution_notes: str = ""
    resource_ids: list[str] = Field(
        default_factory=list,
        description="本次优化实际新增或修订的课程资料标识。",
    )

    @model_validator(mode="after")
    def validate_progress_metadata(self) -> "KnowledgeBaseChangeTask":
        if self.status is not KnowledgeBaseChangeStatus.PENDING:
            if not self.handler:
                raise ValueError("handler is required once a change task leaves pending")
            if self.updated_at is None:
                raise ValueError("updated_at is required once a change task leaves pending")
        if self.status is KnowledgeBaseChangeStatus.WONT_FIX and not self.resolution_notes:
            raise ValueError("resolution_notes is required when closing a change as wont_fix")
        return self


class KnowledgeBaseChangeUpdateRequest(ContractModel):
    """推进或关闭知识库变更任务，构成“审核无效回答 → 优化知识库”的收尾环节。"""

    status: KnowledgeBaseChangeStatus
    handler: str = Field(min_length=1)
    resolution_notes: str = Field(default="", max_length=2000)
    resource_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_transition_request(self) -> "KnowledgeBaseChangeUpdateRequest":
        if self.status is KnowledgeBaseChangeStatus.PENDING:
            raise ValueError("status must move the change task out of pending")
        if self.status is KnowledgeBaseChangeStatus.WONT_FIX and not self.resolution_notes:
            raise ValueError("resolution_notes is required when closing a change as wont_fix")
        return self


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


class ExpectedCitation(ContractModel):
    resource_id: str = Field(min_length=1)
    chunk_id: str | None = Field(default=None, min_length=1)
    chapter: str | None = Field(default=None, min_length=1)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_page_range(self) -> "ExpectedCitation":
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be greater than or equal to page_start")
        return self


class EvaluationAnnotation(ContractModel):
    evaluation_id: str = Field(min_length=1)
    key_points: list[str] = Field(min_length=1)
    expected_citations: list[ExpectedCitation]
    review_status: EvaluationReviewStatus
    reviewer: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str = ""

    @field_validator("key_points")
    @classmethod
    def key_points_must_be_unique_and_non_empty(cls, value: list[str]) -> list[str]:
        if any(not item for item in value):
            raise ValueError("key_points must not contain empty values")
        if len(set(value)) != len(value):
            raise ValueError("key_points must not contain duplicates")
        return value

    @model_validator(mode="after")
    def validate_review_metadata(self) -> "EvaluationAnnotation":
        if self.review_status in {
            EvaluationReviewStatus.APPROVED,
            EvaluationReviewStatus.REJECTED,
        }:
            if not self.reviewer:
                raise ValueError("reviewer is required for approved or rejected annotations")
            if self.reviewed_at is None:
                raise ValueError("reviewed_at is required for approved or rejected annotations")
        return self


class QualityReview(ContractModel):
    review_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    score: int = Field(ge=1, le=5)
    issues: list[str] = Field(default_factory=list)
    notes: str = ""
    reviewed_at: datetime


class QualityReviewRequest(ContractModel):
    chunk_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    score: int = Field(ge=1, le=5)
    issues: list[str] = Field(default_factory=list)
    notes: str = ""


class ApiError(ContractModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    details: dict[str, JsonValue] | None = None


class HealthResponse(ContractModel):
    status: str
    service: str
    mode: str

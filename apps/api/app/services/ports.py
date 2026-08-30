from pathlib import Path
from typing import Protocol

from app.domain.enums import TaskStatus
from app.domain.models import (
    AnswerFeedback,
    AskResponse,
    ChunkMetadata,
    Exercise,
    KnowledgeBaseChangeTask,
    KnowledgePoint,
    LearningEvent,
    QualityReview,
    ResourceImportRequest,
    ResourceImportResponse,
    ResourceSummary,
    TaskTemplate,
)


class ResourceImporter(Protocol):
    def import_resource(self, request: ResourceImportRequest) -> ResourceImportResponse: ...


class FileResourceImporter(Protocol):
    def import_from_file(
        self,
        file_path: Path,
        course_id: str,
        title: str,
        version: str,
        language: str,
        content_type: str,
        knowledge_point_ids: list[str] | None = None,
    ) -> list[ChunkMetadata]: ...


class ChunkStore(Protocol):
    def save(self, chunks: list[ChunkMetadata], course_id: str | None = None) -> int: ...

    def list_by_resource(self, resource_id: str) -> list[ChunkMetadata]: ...

    def list_all(self) -> list[ChunkMetadata]: ...

    def list_resources(self, course_id: str | None = None) -> list[ResourceSummary]: ...

    def count(self) -> int: ...


class Retriever(Protocol):
    def retrieve(self, question: str, course_id: str) -> list[ChunkMetadata]: ...


class AnswerGenerator(Protocol):
    def generate(self, question: str, chunks: list[ChunkMetadata]) -> AskResponse: ...


class KnowledgePointRepository(Protocol):
    def list_knowledge_points(
        self,
        chapter: str | None = None,
        parent_id: str | None = None,
    ) -> list[KnowledgePoint]: ...

    def get_knowledge_point(self, knowledge_point_id: str) -> KnowledgePoint | None: ...


class ExerciseRepository(Protocol):
    def list_exercises(
        self,
        knowledge_point_id: str | None = None,
        exercise_ids: list[str] | None = None,
    ) -> list[Exercise]: ...

    def get_exercise(self, exercise_id: str) -> Exercise | None: ...


class TaskRepository(Protocol):
    def create(self, task: TaskTemplate) -> TaskTemplate: ...

    def list_tasks(self) -> list[TaskTemplate]: ...

    def get_task(self, task_id: str) -> TaskTemplate | None: ...

    def update_status(self, task_id: str, status: TaskStatus) -> TaskTemplate | None: ...


class EventSink(Protocol):
    def record(self, event: LearningEvent) -> LearningEvent: ...

    def query(
        self,
        *,
        course_id: str | None = None,
        user_id: str | None = None,
        event_type: str | None = None,
        object_id: str | None = None,
    ) -> list[LearningEvent]: ...


class FeedbackStore(Protocol):
    def create(self, feedback: AnswerFeedback) -> AnswerFeedback: ...

    def get(self, feedback_id: str) -> AnswerFeedback | None: ...

    def list_all(self) -> list[AnswerFeedback]: ...

    def replace(self, feedback: AnswerFeedback) -> AnswerFeedback: ...


class KnowledgeBaseChangeStore(Protocol):
    def create(self, change: KnowledgeBaseChangeTask) -> KnowledgeBaseChangeTask: ...

    def get(self, change_id: str) -> KnowledgeBaseChangeTask | None: ...

    def list_all(self) -> list[KnowledgeBaseChangeTask]: ...

    def replace(self, change: KnowledgeBaseChangeTask) -> KnowledgeBaseChangeTask: ...


class QualityReviewStore(Protocol):
    def save(self, review: QualityReview) -> QualityReview: ...

    def list_all(self) -> list[QualityReview]: ...

    def list_by_chunk(self, chunk_id: str) -> list[QualityReview]: ...

    def get(self, review_id: str) -> QualityReview | None: ...

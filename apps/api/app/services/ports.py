from pathlib import Path
from typing import Protocol

from app.domain.models import (
    AskResponse,
    ChunkMetadata,
    LearningEvent,
    QualityReview,
    ResourceImportRequest,
    ResourceImportResponse,
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
    def save(self, chunks: list[ChunkMetadata]) -> int: ...

    def list_by_resource(self, resource_id: str) -> list[ChunkMetadata]: ...

    def list_all(self) -> list[ChunkMetadata]: ...

    def count(self) -> int: ...


class Retriever(Protocol):
    def retrieve(self, question: str, course_id: str) -> list[ChunkMetadata]: ...


class AnswerGenerator(Protocol):
    def generate(self, question: str, chunks: list[ChunkMetadata]) -> AskResponse: ...


class TaskRepository(Protocol):
    def list_tasks(self) -> list[TaskTemplate]: ...

    def get_task(self, task_id: str) -> TaskTemplate | None: ...


class EventSink(Protocol):
    def record(self, event: LearningEvent) -> LearningEvent: ...


class QualityReviewStore(Protocol):
    def save(self, review: QualityReview) -> QualityReview: ...

    def list_all(self) -> list[QualityReview]: ...

    def list_by_chunk(self, chunk_id: str) -> list[QualityReview]: ...

    def get(self, review_id: str) -> QualityReview | None: ...

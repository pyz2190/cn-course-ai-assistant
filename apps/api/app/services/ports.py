from typing import Protocol

from app.domain.models import (
    AskResponse,
    ChunkMetadata,
    LearningEvent,
    ResourceImportRequest,
    ResourceImportResponse,
    TaskTemplate,
)


class ResourceImporter(Protocol):
    def import_resource(self, request: ResourceImportRequest) -> ResourceImportResponse: ...


class Retriever(Protocol):
    def retrieve(self, question: str, course_id: str) -> list[ChunkMetadata]: ...


class AnswerGenerator(Protocol):
    def generate(self, question: str, chunks: list[ChunkMetadata]) -> AskResponse: ...


class TaskRepository(Protocol):
    def list_tasks(self) -> list[TaskTemplate]: ...

    def get_task(self, task_id: str) -> TaskTemplate | None: ...


class EventSink(Protocol):
    def record(self, event: LearningEvent) -> LearningEvent: ...

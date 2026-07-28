from functools import lru_cache

from app.adapters.mock import (
    InMemoryEventSink,
    InMemoryTaskRepository,
    MockAnswerGenerator,
    MockResourceImporter,
    MockRetriever,
)
from app.services.ports import EventSink, ResourceImporter, TaskRepository
from app.services.qa import QaService


@lru_cache
def get_resource_importer() -> ResourceImporter:
    return MockResourceImporter()


@lru_cache
def get_qa_service() -> QaService:
    return QaService(MockRetriever(), MockAnswerGenerator())


@lru_cache
def get_task_repository() -> TaskRepository:
    return InMemoryTaskRepository()


@lru_cache
def get_event_sink() -> EventSink:
    return InMemoryEventSink()

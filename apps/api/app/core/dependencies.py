from functools import lru_cache

from app.adapters.mock import (
    InMemoryChunkStore,
    InMemoryEventSink,
    InMemoryQualityReviewStore,
    InMemoryTaskRepository,
    MockAnswerGenerator,
    MockResourceImporter,
    MockRetriever,
)
from app.core.config import get_settings
from app.services.ports import (
    ChunkStore,
    EventSink,
    QualityReviewStore,
    ResourceImporter,
    TaskRepository,
)
from app.services.qa import QaService

_chunk_store = InMemoryChunkStore()
_quality_review_store = InMemoryQualityReviewStore()


@lru_cache
def get_resource_importer() -> ResourceImporter:
    # /resources/import 仅接收元数据，使用 Mock 适配器。
    # 真实文件解析请使用 /resources/upload 端点。
    return MockResourceImporter()


@lru_cache
def get_chunk_store() -> ChunkStore:
    return _chunk_store


@lru_cache
def get_file_importer():
    settings = get_settings()
    if settings.resource_importer == "real":
        from pathlib import Path

        from app.adapters.document_parser import RealResourceImporter

        return RealResourceImporter(storage_dir=Path(settings.resource_storage_dir))
    return None


@lru_cache
def get_qa_service() -> QaService:
    return QaService(MockRetriever(), MockAnswerGenerator())


@lru_cache
def get_task_repository() -> TaskRepository:
    return InMemoryTaskRepository()


@lru_cache
def get_event_sink() -> EventSink:
    return InMemoryEventSink()


@lru_cache
def get_quality_review_store() -> QualityReviewStore:
    return _quality_review_store

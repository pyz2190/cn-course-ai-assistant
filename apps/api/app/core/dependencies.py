from functools import lru_cache

import httpx2

from app.adapters.knowledge_points import InMemoryKnowledgePointRepository
from app.adapters.mock import (
    MOCK_CHUNKS,
    InMemoryChunkStore,
    InMemoryEventSink,
    InMemoryFeedbackStore,
    InMemoryKnowledgeBaseChangeStore,
    InMemoryQualityReviewStore,
    InMemoryTaskRepository,
    MockResourceImporter,
)
from app.adapters.rag.embeddings import BgeM3Embedding, OfflineHashEmbedding
from app.adapters.rag.generators import OfflineExtractiveGenerator, OpenAICompatibleGenerator
from app.adapters.rag.qdrant_store import QdrantVectorStore, create_qdrant_client
from app.adapters.rag.rerankers import BgeReranker, OfflineOverlapReranker
from app.core.config import get_settings
from app.services.ports import (
    ChunkStore,
    EventSink,
    FeedbackStore,
    KnowledgeBaseChangeStore,
    KnowledgePointRepository,
    QualityReviewStore,
    ResourceImporter,
    TaskRepository,
)
from app.services.qa import QaService
from app.services.rag import IndexManager, RagService, RetrievalPipeline

_quality_review_store = InMemoryQualityReviewStore()


@lru_cache
def get_resource_importer() -> ResourceImporter:
    return MockResourceImporter()


@lru_cache
def get_rag_service() -> RagService:
    settings = get_settings()
    embedding = (
        BgeM3Embedding(settings.embedding_model)
        if settings.embedding_provider == "bge"
        else OfflineHashEmbedding(settings.offline_embedding_dimension)
    )
    client = create_qdrant_client(
        settings.vector_store,
        path=settings.qdrant_path,
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None,
    )
    store = QdrantVectorStore(client, f"{settings.qdrant_collection_prefix}_computer_networks")
    reranker = (
        None
        if not settings.reranker_enabled
        else (
            BgeReranker(settings.reranker_model)
            if settings.reranker_provider == "bge"
            else OfflineOverlapReranker()
        )
    )
    offline_generator = OfflineExtractiveGenerator()
    if settings.generator_provider == "openai-compatible":
        generator = OpenAICompatibleGenerator(
            base_url=settings.model_base_url or "",
            model_id=settings.generator_model,
            api_key=settings.model_api_key.get_secret_value() if settings.model_api_key else None,
            timeout=httpx2.Timeout(
                connect=settings.connect_timeout_seconds,
                read=settings.read_timeout_seconds,
                write=settings.write_timeout_seconds,
                pool=settings.pool_timeout_seconds,
            ),
            max_retries=settings.max_retries,
        )
    else:
        generator = offline_generator
    service = RagService(
        IndexManager(embedding, store),
        RetrievalPipeline(
            embedding,
            store,
            reranker,
            min_score=settings.min_retrieval_score,
            allow_degraded=settings.allow_degraded,
        ),
        generator,
        mode=settings.mode,
        top_k=settings.top_k,
        fetch_k=settings.fetch_k,
        allow_degraded=settings.allow_degraded,
        fallback_generator=offline_generator if generator is not offline_generator else None,
    )
    service.index_course("computer-networks", MOCK_CHUNKS)
    return service


@lru_cache
def get_chunk_store() -> ChunkStore:
    return InMemoryChunkStore()


@lru_cache
def get_file_importer():
    settings = get_settings()
    if settings.resource_importer == "real":
        from app.adapters.document_parser import RealResourceImporter

        return RealResourceImporter(storage_dir=settings.resource_storage_dir)
    return None


@lru_cache
def get_qa_service() -> QaService:
    return QaService(get_rag_service())


@lru_cache
def get_knowledge_point_repository() -> KnowledgePointRepository:
    return InMemoryKnowledgePointRepository()


@lru_cache
def get_task_repository() -> TaskRepository:
    return InMemoryTaskRepository()


@lru_cache
def get_event_sink() -> EventSink:
    return InMemoryEventSink()


@lru_cache
def get_feedback_store() -> FeedbackStore:
    return InMemoryFeedbackStore()


@lru_cache
def get_knowledge_base_change_store() -> KnowledgeBaseChangeStore:
    return InMemoryKnowledgeBaseChangeStore()


@lru_cache
def get_quality_review_store() -> QualityReviewStore:
    return _quality_review_store

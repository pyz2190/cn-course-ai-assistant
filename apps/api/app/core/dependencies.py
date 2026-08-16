from functools import lru_cache

import httpx2

from app.adapters.mock import (
    MOCK_CHUNKS,
    InMemoryEventSink,
    InMemoryTaskRepository,
    MockResourceImporter,
)
from app.adapters.rag.embeddings import BgeM3Embedding, OfflineHashEmbedding
from app.adapters.rag.generators import (
    OfflineExtractiveGenerator,
    OpenAICompatibleGenerator,
)
from app.adapters.rag.qdrant_store import QdrantVectorStore, create_qdrant_client
from app.adapters.rag.rerankers import BgeReranker, OfflineOverlapReranker
from app.core.config import get_settings
from app.services.ports import EventSink, ResourceImporter, TaskRepository
from app.services.qa import QaService
from app.services.rag import IndexManager, RagService, RetrievalPipeline


@lru_cache
def get_resource_importer() -> ResourceImporter:
    return MockResourceImporter()


@lru_cache
def get_rag_service() -> RagService:
    settings = get_settings()
    if settings.embedding_provider == "bge":
        embedding = BgeM3Embedding(settings.embedding_model)
    else:
        embedding = OfflineHashEmbedding(settings.offline_embedding_dimension)

    client = create_qdrant_client(
        settings.vector_store,
        path=settings.qdrant_path,
        url=settings.qdrant_url,
        api_key=(
            settings.qdrant_api_key.get_secret_value()
            if settings.qdrant_api_key
            else None
        ),
    )
    store = QdrantVectorStore(
        client,
        f"{settings.qdrant_collection_prefix}_computer_networks",
    )
    if not settings.reranker_enabled:
        reranker = None
    elif settings.reranker_provider == "bge":
        reranker = BgeReranker(settings.reranker_model)
    else:
        reranker = OfflineOverlapReranker()

    offline_generator = OfflineExtractiveGenerator()
    if settings.generator_provider == "openai-compatible":
        timeout = httpx2.Timeout(
            connect=settings.connect_timeout_seconds,
            read=settings.read_timeout_seconds,
            write=settings.write_timeout_seconds,
            pool=settings.pool_timeout_seconds,
        )
        generator = OpenAICompatibleGenerator(
            base_url=settings.model_base_url or "",
            model_id=settings.generator_model,
            api_key=(
                settings.model_api_key.get_secret_value()
                if settings.model_api_key
                else None
            ),
            timeout=timeout,
            max_retries=settings.max_retries,
        )
    else:
        generator = offline_generator

    index_manager = IndexManager(embedding, store)
    retrieval = RetrievalPipeline(
        embedding,
        store,
        reranker,
        min_score=settings.min_retrieval_score,
        allow_degraded=settings.allow_degraded,
    )
    service = RagService(
        index_manager,
        retrieval,
        generator,
        mode=settings.mode,
        top_k=settings.top_k,
        fetch_k=settings.fetch_k,
        allow_degraded=settings.allow_degraded,
        fallback_generator=(
            offline_generator if generator is not offline_generator else None
        ),
    )
    service.index_course("computer-networks", MOCK_CHUNKS)
    return service


@lru_cache
def get_qa_service() -> QaService:
    return QaService(get_rag_service())


@lru_cache
def get_task_repository() -> TaskRepository:
    return InMemoryTaskRepository()


@lru_cache
def get_event_sink() -> EventSink:
    return InMemoryEventSink()

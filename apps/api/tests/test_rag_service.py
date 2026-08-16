from qdrant_client import QdrantClient

from app.adapters.mock import MOCK_CHUNKS
from app.adapters.rag.embeddings import OfflineHashEmbedding
from app.adapters.rag.generators import OfflineExtractiveGenerator
from app.adapters.rag.qdrant_store import QdrantVectorStore
from app.adapters.rag.rerankers import OfflineOverlapReranker
from app.domain.models import AskRequest
from app.domain.rag import RagExecutionOptions, RetrievalScope
from app.services.qa import QaService
from app.services.rag import IndexManager, RagService, RetrievalPipeline


class BrokenGenerator:
    model_id = "broken-generator"

    def generate(self, question, evidence):
        raise TimeoutError("generator timed out")


def _service(*, min_score: float = 0, broken_generator: bool = False) -> RagService:
    embedding = OfflineHashEmbedding(dimension=128)
    store = QdrantVectorStore(QdrantClient(location=":memory:"), "service_chunks")
    index_manager = IndexManager(embedding, store)
    retrieval = RetrievalPipeline(
        embedding,
        store,
        OfflineOverlapReranker(),
        min_score=min_score,
        allow_degraded=True,
    )
    offline = OfflineExtractiveGenerator()
    service = RagService(
        index_manager,
        retrieval,
        BrokenGenerator() if broken_generator else offline,
        mode="offline",
        top_k=3,
        fetch_k=8,
        allow_degraded=True,
        fallback_generator=offline if broken_generator else None,
    )
    service.index_course("computer-networks", MOCK_CHUNKS)
    return service


def test_service_returns_grounded_answer_and_runtime() -> None:
    result = _service().answer(
        "TCP 为什么需要三次握手？",
        RetrievalScope(course_id="computer-networks"),
    )

    assert result.citations
    assert "[1]" in result.answer
    assert result.citations[0].chunk_id == "chunk-transport-tcp-001"
    assert result.runtime.embedding.startswith("offline-hash-v1")
    assert result.runtime.corpus_version != "unindexed"
    assert result.degraded is False


def test_service_refuses_when_relevance_is_too_low() -> None:
    result = _service(min_score=2).answer(
        "量子纠缠如何用于星际通信？",
        RetrievalScope(course_id="computer-networks"),
    )

    assert result.citations == ()
    assert result.confidence == 0
    assert result.degraded is True
    assert "没有足够证据" in result.answer


def test_service_falls_back_after_generator_timeout() -> None:
    result = _service(broken_generator=True).answer(
        "DNS 递归查询是什么？",
        RetrievalScope(course_id="computer-networks"),
    )

    assert result.citations
    assert result.degraded is True
    assert result.runtime.model == "offline-extractive-v1"


def test_service_rejects_unavailable_requested_component() -> None:
    service = _service()

    try:
        service.answer(
            "TCP",
            RetrievalScope(course_id="computer-networks"),
            RagExecutionOptions(model="not-configured"),
        )
    except ValueError as error:
        assert "unavailable" in str(error)
    else:
        raise AssertionError("unavailable component was accepted")


class CapturingRagService:
    def __init__(self, result) -> None:
        self.result = result
        self.call = None

    def answer(self, question, scope, options=None):
        self.call = (question, scope, options)
        return self.result


def test_qa_service_maps_scope_without_forwarding_user_id() -> None:
    base_result = _service().answer(
        "TCP",
        RetrievalScope(course_id="computer-networks"),
    )
    rag = CapturingRagService(base_result)
    qa = QaService(rag)  # type: ignore[arg-type]
    request = AskRequest(
        course_id="computer-networks",
        user_id="private-user-id",
        question="TCP",
        knowledge_point_ids=["kp-transport-tcp-handshake"],
        resource_ids=["resource-000"],
        task_id="task-protocol-tcp-handshake",
    )

    response = qa.ask(request)

    question, scope, options = rag.call
    assert question == "TCP"
    assert scope.course_id == "computer-networks"
    assert scope.knowledge_point_ids == ("kp-transport-tcp-handshake",)
    assert scope.resource_ids == ("resource-000",)
    assert scope.task_id == "task-protocol-tcp-handshake"
    assert options is None
    assert "private-user-id" not in repr(rag.call)
    assert response.citations

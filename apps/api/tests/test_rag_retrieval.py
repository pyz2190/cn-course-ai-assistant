from dataclasses import replace

import pytest
from qdrant_client import QdrantClient

from app.adapters.mock import MOCK_CHUNKS
from app.adapters.rag.embeddings import BgeM3Embedding, OfflineHashEmbedding
from app.adapters.rag.qdrant_store import QdrantVectorStore
from app.adapters.rag.rerankers import BgeReranker, OfflineOverlapReranker
from app.domain.rag import RetrievalQuery, RetrievalScope, RetrievedChunk
from app.services.rag import IndexManager, RetrievalPipeline


@pytest.fixture
def pipeline() -> RetrievalPipeline:
    embedding = OfflineHashEmbedding(dimension=128)
    store = QdrantVectorStore(QdrantClient(location=":memory:"), "retrieval_chunks")
    IndexManager(embedding, store).index_course("computer-networks", MOCK_CHUNKS)
    return RetrievalPipeline(
        embedding,
        store,
        OfflineOverlapReranker(),
        min_score=0,
        allow_degraded=True,
    )


@pytest.mark.parametrize(
    ("question", "expected_chunk"),
    [
        ("TCP 为什么需要三次握手？", "chunk-transport-tcp-001"),
        ("DNS 递归查询是什么？", "chunk-app-dns-001"),
        ("HTTP 请求报文包含什么？", "chunk-app-http-001"),
        ("RIP、OSPF 和 BGP 属于什么路由协议？", "chunk-network-routing-001"),
        ("如何使用 Wireshark 捕获 TCP 三次握手？", "chunk-lab-wireshark-001"),
    ],
)
def test_retrieves_expected_topic(
    pipeline: RetrievalPipeline,
    question: str,
    expected_chunk: str,
) -> None:
    outcome = pipeline.retrieve(
        RetrievalQuery(
            question=question,
            scope=RetrievalScope(course_id="computer-networks"),
            top_k=3,
            fetch_k=8,
        )
    )

    assert outcome.chunks[0].chunk.chunk_id == expected_chunk
    assert outcome.reranker_applied is True


def test_filters_by_knowledge_point_and_resource(pipeline: RetrievalPipeline) -> None:
    by_knowledge = pipeline.retrieve(
        RetrievalQuery(
            question="DNS 查询",
            scope=RetrievalScope(
                course_id="computer-networks",
                knowledge_point_ids=("kp-application-dns",),
            ),
            top_k=10,
            fetch_k=10,
        )
    )
    assert by_knowledge.chunks
    assert all(
        "kp-application-dns" in item.chunk.knowledge_point_ids
        for item in by_knowledge.chunks
    )

    resource_id = MOCK_CHUNKS[-1].resource_id
    by_resource = pipeline.retrieve(
        RetrievalQuery(
            question="DNS 实验",
            scope=RetrievalScope(
                course_id="computer-networks",
                resource_ids=(resource_id,),
            ),
            top_k=10,
            fetch_k=10,
        )
    )
    assert by_resource.chunks
    assert all(item.chunk.resource_id == resource_id for item in by_resource.chunks)


class BrokenReranker:
    model_id = "broken"

    def rerank(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        limit: int,
    ) -> list[RetrievedChunk]:
        raise TimeoutError("reranker timed out")


def test_reranker_failure_returns_unreranked_candidates() -> None:
    embedding = OfflineHashEmbedding(dimension=64)
    store = QdrantVectorStore(QdrantClient(location=":memory:"), "fallback_chunks")
    IndexManager(embedding, store).index_course("computer-networks", MOCK_CHUNKS)
    pipeline = RetrievalPipeline(
        embedding,
        store,
        BrokenReranker(),
        min_score=0,
        allow_degraded=True,
    )

    outcome = pipeline.retrieve(
        RetrievalQuery(
            question="TCP 握手",
            scope=RetrievalScope(course_id="computer-networks"),
            top_k=3,
            fetch_k=8,
        )
    )

    assert outcome.chunks
    assert outcome.reranker_applied is False
    assert all(item.rerank_score is None for item in outcome.chunks)


def test_disabled_reranker_is_reported() -> None:
    embedding = OfflineHashEmbedding(dimension=64)
    store = QdrantVectorStore(QdrantClient(location=":memory:"), "disabled_chunks")
    IndexManager(embedding, store).index_course("computer-networks", MOCK_CHUNKS)
    pipeline = RetrievalPipeline(
        embedding,
        store,
        None,
        min_score=0,
        allow_degraded=True,
    )

    outcome = pipeline.retrieve(
        RetrievalQuery(
            question="TCP",
            scope=RetrievalScope(course_id="computer-networks"),
            top_k=2,
            fetch_k=3,
        )
    )

    assert outcome.reranker_applied is False
    assert len(outcome.chunks) == 2


class FakeEmbeddingModel:
    def __init__(self, model_id: str, use_fp16: bool) -> None:
        self.model_id = model_id
        self.use_fp16 = use_fp16

    def encode(
        self,
        texts: list[str],
        batch_size: int,
        normalize_embeddings: bool,
    ) -> dict[str, list[list[float]]]:
        assert batch_size == 8
        assert normalize_embeddings is True
        return {"dense_vecs": [[float(len(text)), 1.0] for text in texts]}


def test_bge_embedding_uses_injected_loader_without_download() -> None:
    embedding = BgeM3Embedding(
        model_id="test-bge",
        dimension=2,
        loader=FakeEmbeddingModel,
    )

    assert embedding.embed_documents(["TCP", "DNS"]) == [[3.0, 1.0], [3.0, 1.0]]
    assert embedding.model_id == "test-bge"


class FakeRerankerModel:
    def __init__(self, model_id: str, use_fp16: bool) -> None:
        self.model_id = model_id
        self.use_fp16 = use_fp16

    def compute_score(
        self,
        pairs: list[list[str]],
        normalize: bool,
    ) -> list[float]:
        assert normalize is True
        return [0.2, 0.8]


def test_bge_reranker_maps_scores_without_download() -> None:
    chunks = [
        RetrievedChunk(MOCK_CHUNKS[0], retrieval_score=0.9, final_score=0.9),
        RetrievedChunk(MOCK_CHUNKS[1], retrieval_score=0.3, final_score=0.3),
    ]
    reranker = BgeReranker(model_id="test-reranker", loader=FakeRerankerModel)

    result = reranker.rerank("DNS", chunks, limit=2)

    assert result[0] == replace(chunks[1], rerank_score=0.8, final_score=0.8)
    assert result[1].rerank_score == 0.2

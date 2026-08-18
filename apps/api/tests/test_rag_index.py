import math

from qdrant_client import QdrantClient

from app.adapters.mock import MOCK_CHUNKS
from app.adapters.rag.embeddings import OfflineHashEmbedding
from app.adapters.rag.qdrant_store import QdrantVectorStore
from app.services.rag import IndexManager, corpus_fingerprint


class CountingEmbedding(OfflineHashEmbedding):
    def __init__(self) -> None:
        super().__init__(dimension=64)
        self.document_calls = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_calls += 1
        return super().embed_documents(texts)


def test_offline_embedding_is_deterministic_and_normalized() -> None:
    first = OfflineHashEmbedding(dimension=64).embed_query("TCP 三次握手")
    second = OfflineHashEmbedding(dimension=64).embed_query("TCP 三次握手")

    assert first == second
    assert math.isclose(math.sqrt(sum(value * value for value in first)), 1.0)


def test_fingerprint_is_order_independent_and_content_sensitive() -> None:
    embedding_id = "offline-test"
    original = corpus_fingerprint(MOCK_CHUNKS, embedding_id)
    reordered = corpus_fingerprint(list(reversed(MOCK_CHUNKS)), embedding_id)
    changed_chunks = [
        MOCK_CHUNKS[0].model_copy(update={"content": "changed"}),
        *MOCK_CHUNKS[1:],
    ]

    assert original == reordered
    assert original != corpus_fingerprint(changed_chunks, embedding_id)


def test_index_is_idempotent_and_preserves_all_metadata() -> None:
    embedding = CountingEmbedding()
    store = QdrantVectorStore(QdrantClient(location=":memory:"), "test_chunks")
    manager = IndexManager(embedding, store)

    first = manager.index_course("computer-networks", MOCK_CHUNKS)
    second = manager.index_course("computer-networks", MOCK_CHUNKS)

    assert first.indexed_chunks == len(MOCK_CHUNKS)
    assert first.reused_existing_index is False
    assert second.indexed_chunks == len(MOCK_CHUNKS)
    assert second.reused_existing_index is True
    assert embedding.document_calls == 1


def test_repeated_upsert_does_not_duplicate_points() -> None:
    embedding = OfflineHashEmbedding(dimension=64)
    store = QdrantVectorStore(QdrantClient(location=":memory:"), "upsert_chunks")
    vectors = embedding.embed_documents([chunk.content for chunk in MOCK_CHUNKS])
    store.ensure_index(embedding.dimension)

    store.upsert("computer-networks", MOCK_CHUNKS, vectors)
    store.upsert("computer-networks", MOCK_CHUNKS, vectors)

    assert store.count() == len(MOCK_CHUNKS)

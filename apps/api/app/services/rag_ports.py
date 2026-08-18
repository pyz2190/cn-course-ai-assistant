from typing import Protocol

from app.domain.models import ChunkMetadata
from app.domain.rag import GenerationDraft, RetrievalScope, RetrievedChunk


class EmbeddingProvider(Protocol):
    @property
    def model_id(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    @property
    def store_id(self) -> str: ...

    def ensure_index(self, dimension: int) -> None: ...

    def count(self) -> int: ...

    def upsert(
        self,
        course_id: str,
        chunks: list[ChunkMetadata],
        vectors: list[list[float]],
    ) -> None: ...

    def search(
        self,
        query_vector: list[float],
        scope: RetrievalScope,
        limit: int,
    ) -> list[RetrievedChunk]: ...


class Reranker(Protocol):
    @property
    def model_id(self) -> str: ...

    def rerank(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        limit: int,
    ) -> list[RetrievedChunk]: ...


class GroundedGenerator(Protocol):
    @property
    def model_id(self) -> str: ...

    def generate(
        self,
        question: str,
        evidence: list[RetrievedChunk],
    ) -> GenerationDraft: ...

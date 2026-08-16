import hashlib
import json
from dataclasses import dataclass
from time import perf_counter

from app.domain.models import ChunkMetadata
from app.domain.rag import (
    IndexSummary,
    RetrievalQuery,
    RetrievedChunk,
)
from app.services.rag_ports import EmbeddingProvider, Reranker, VectorStore


def corpus_fingerprint(chunks: list[ChunkMetadata], embedding_id: str) -> str:
    payload = {
        "embedding": embedding_id,
        "chunks": sorted(
            (chunk.model_dump(mode="json") for chunk in chunks),
            key=lambda item: item["chunk_id"],
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class IndexManager:
    def __init__(self, embedding: EmbeddingProvider, store: VectorStore) -> None:
        self._embedding = embedding
        self._store = store
        self._fingerprints: dict[str, str] = {}

    def index_course(self, course_id: str, chunks: list[ChunkMetadata]) -> IndexSummary:
        fingerprint = corpus_fingerprint(chunks, self._embedding.model_id)
        self._store.ensure_index(self._embedding.dimension)
        reused = (
            self._fingerprints.get(course_id) == fingerprint
            and self._store.count() == len(chunks)
        )
        if not reused:
            vectors = self._embedding.embed_documents(
                [self._embedding_text(chunk) for chunk in chunks]
            )
            self._store.upsert(course_id, chunks, vectors)
            self._fingerprints[course_id] = fingerprint
        return IndexSummary(
            course_id=course_id,
            indexed_chunks=self._store.count(),
            collection_name=self._store.store_id,
            corpus_version=fingerprint,
            embedding=self._embedding.model_id,
            reused_existing_index=reused,
        )

    @staticmethod
    def _embedding_text(chunk: ChunkMetadata) -> str:
        return "\n".join(
            [
                chunk.title,
                chunk.chapter,
                " ".join(chunk.knowledge_point_ids),
                chunk.content,
            ]
        )


@dataclass(frozen=True)
class RetrievalOutcome:
    chunks: tuple[RetrievedChunk, ...]
    retrieval_ms: float
    rerank_ms: float
    reranker_applied: bool


class RetrievalPipeline:
    def __init__(
        self,
        embedding: EmbeddingProvider,
        store: VectorStore,
        reranker: Reranker | None,
        *,
        min_score: float,
        allow_degraded: bool,
    ) -> None:
        self._embedding = embedding
        self._store = store
        self._reranker = reranker
        self._min_score = min_score
        self._allow_degraded = allow_degraded

    @property
    def embedding_id(self) -> str:
        return self._embedding.model_id

    @property
    def vector_store_id(self) -> str:
        return self._store.store_id

    @property
    def reranker_id(self) -> str:
        return self._reranker.model_id if self._reranker else "disabled"

    def retrieve(self, query: RetrievalQuery) -> RetrievalOutcome:
        retrieval_start = perf_counter()
        vector = self._embedding.embed_query(query.question)
        candidates = self._store.search(vector, query.scope, query.fetch_k)
        candidates = [item for item in candidates if item.retrieval_score >= self._min_score]
        retrieval_ms = (perf_counter() - retrieval_start) * 1000

        if not self._reranker:
            return RetrievalOutcome(
                chunks=tuple(candidates[: query.top_k]),
                retrieval_ms=retrieval_ms,
                rerank_ms=0,
                reranker_applied=False,
            )
        rerank_start = perf_counter()
        try:
            reranked = self._reranker.rerank(query.question, candidates, query.top_k)
        except Exception:
            if not self._allow_degraded:
                raise
            return RetrievalOutcome(
                chunks=tuple(candidates[: query.top_k]),
                retrieval_ms=retrieval_ms,
                rerank_ms=(perf_counter() - rerank_start) * 1000,
                reranker_applied=False,
            )
        return RetrievalOutcome(
            chunks=tuple(reranked),
            retrieval_ms=retrieval_ms,
            rerank_ms=(perf_counter() - rerank_start) * 1000,
            reranker_applied=True,
        )

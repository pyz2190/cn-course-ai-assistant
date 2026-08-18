from dataclasses import dataclass

from app.domain.enums import AccessLevel
from app.domain.models import ChunkMetadata, Citation


@dataclass(frozen=True)
class RetrievalScope:
    course_id: str
    knowledge_point_ids: tuple[str, ...] = ()
    resource_ids: tuple[str, ...] = ()
    task_id: str | None = None
    allowed_access_levels: tuple[AccessLevel, ...] = (AccessLevel.COURSE,)


@dataclass(frozen=True)
class RetrievalQuery:
    question: str
    scope: RetrievalScope
    top_k: int
    fetch_k: int


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: ChunkMetadata
    retrieval_score: float
    rerank_score: float | None = None
    final_score: float = 0.0


@dataclass(frozen=True)
class GroundedSentence:
    text: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class GenerationDraft:
    sentences: tuple[GroundedSentence, ...]
    resolved_model: str
    degraded: bool


@dataclass(frozen=True)
class RagRuntime:
    mode: str
    embedding: str
    vector_store: str
    reranker: str
    model: str
    top_k: int
    fetch_k: int
    retrieval_ms: float
    rerank_ms: float
    generation_ms: float
    corpus_version: str


@dataclass(frozen=True)
class RagResult:
    answer: str
    citations: tuple[Citation, ...]
    confidence: float
    degraded: bool
    runtime: RagRuntime


@dataclass(frozen=True)
class IndexSummary:
    course_id: str
    indexed_chunks: int
    collection_name: str
    corpus_version: str
    embedding: str
    reused_existing_index: bool


@dataclass(frozen=True)
class RagExecutionOptions:
    model: str | None = None
    embedding: str | None = None
    reranker: str | None = None
    top_k: int | None = None

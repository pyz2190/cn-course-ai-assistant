import hashlib
import json
from dataclasses import dataclass, replace
from time import perf_counter

from app.domain.models import ChunkMetadata, Citation
from app.domain.rag import (
    GenerationDraft,
    IndexSummary,
    RagExecutionOptions,
    RagResult,
    RagRuntime,
    RetrievalQuery,
    RetrievalScope,
    RetrievedChunk,
)
from app.services.rag_ports import (
    EmbeddingProvider,
    GroundedGenerator,
    Reranker,
    VectorStore,
)


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
        self._corpora: dict[str, list[ChunkMetadata]] = {}

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
        self._corpora[course_id] = list(chunks)
        return IndexSummary(
            course_id=course_id,
            indexed_chunks=self._store.count(),
            collection_name=self._store.store_id,
            corpus_version=fingerprint,
            embedding=self._embedding.model_id,
            reused_existing_index=reused,
        )

    def index_chunks(self, course_id: str, chunks: list[ChunkMetadata]) -> IndexSummary:
        """增量向量化新导入的资料，使其立即可被检索，不重建既有索引。

        点 ID 由 `course_id` 与 `chunk_id` 决定，重复导入同一 Chunk 会覆盖而非追加。
        """
        self._store.ensure_index(self._embedding.dimension)
        if chunks:
            vectors = self._embedding.embed_documents(
                [self._embedding_text(chunk) for chunk in chunks]
            )
            self._store.upsert(course_id, chunks, vectors)

        corpus = self._corpora.setdefault(course_id, [])
        indexed_ids = {chunk.chunk_id for chunk in corpus}
        corpus.extend(chunk for chunk in chunks if chunk.chunk_id not in indexed_ids)
        fingerprint = corpus_fingerprint(corpus, self._embedding.model_id)
        self._fingerprints[course_id] = fingerprint

        return IndexSummary(
            course_id=course_id,
            indexed_chunks=self._store.count(),
            collection_name=self._store.store_id,
            corpus_version=fingerprint,
            embedding=self._embedding.model_id,
            reused_existing_index=False,
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
        retrieval_ms = (perf_counter() - retrieval_start) * 1000

        if not self._reranker:
            filtered = [
                item for item in candidates if item.retrieval_score >= self._min_score
            ]
            return RetrievalOutcome(
                chunks=tuple(filtered[: query.top_k]),
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
            filtered = [
                item for item in candidates if item.retrieval_score >= self._min_score
            ]
            return RetrievalOutcome(
                chunks=tuple(filtered[: query.top_k]),
                retrieval_ms=retrieval_ms,
                rerank_ms=(perf_counter() - rerank_start) * 1000,
                reranker_applied=False,
            )
        filtered = [item for item in reranked if item.final_score >= self._min_score]
        return RetrievalOutcome(
            chunks=tuple(filtered),
            retrieval_ms=retrieval_ms,
            rerank_ms=(perf_counter() - rerank_start) * 1000,
            reranker_applied=True,
        )


@dataclass(frozen=True)
class AssembledAnswer:
    answer: str
    citations: tuple[Citation, ...]


class CitationAssembler:
    def assemble(
        self,
        draft: GenerationDraft,
        evidence: tuple[RetrievedChunk, ...],
    ) -> AssembledAnswer:
        evidence_by_id = {item.chunk.chunk_id: item for item in evidence}
        citation_numbers: dict[str, int] = {}
        answer_sentences: list[str] = []
        for sentence in draft.sentences:
            valid_ids = tuple(
                evidence_id
                for evidence_id in sentence.evidence_ids
                if evidence_id in evidence_by_id
            )
            if not valid_ids:
                continue
            markers: list[str] = []
            for evidence_id in valid_ids:
                if evidence_id not in citation_numbers:
                    citation_numbers[evidence_id] = len(citation_numbers) + 1
                markers.append(f"[{citation_numbers[evidence_id]}]")
            answer_sentences.append(f"{sentence.text}{''.join(markers)}")

        citations = tuple(
            self._citation(citation_number, evidence_by_id[evidence_id])
            for evidence_id, citation_number in sorted(
                citation_numbers.items(), key=lambda item: item[1]
            )
        )
        return AssembledAnswer("".join(answer_sentences), citations)

    @staticmethod
    def _citation(number: int, item: RetrievedChunk) -> Citation:
        chunk = item.chunk
        return Citation(
            citation_id=f"citation-{number}",
            chunk_id=chunk.chunk_id,
            resource_id=chunk.resource_id,
            title=chunk.title,
            chapter=chunk.chapter,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            quote=chunk.content,
            source_url=chunk.source_url,
            retrieval_score=item.retrieval_score,
            rerank_score=item.rerank_score,
        )


class RagService:
    def __init__(
        self,
        index_manager: IndexManager,
        retrieval: RetrievalPipeline,
        generator: GroundedGenerator,
        *,
        mode: str,
        top_k: int,
        fetch_k: int,
        allow_degraded: bool,
        fallback_generator: GroundedGenerator | None = None,
        citation_assembler: CitationAssembler | None = None,
    ) -> None:
        self._index_manager = index_manager
        self._retrieval = retrieval
        self._generator = generator
        self._fallback_generator = fallback_generator
        self._mode = mode
        self._top_k = top_k
        self._fetch_k = fetch_k
        self._allow_degraded = allow_degraded
        self._citation_assembler = citation_assembler or CitationAssembler()
        self._corpus_versions: dict[str, str] = {}

    def index_course(self, course_id: str, chunks: list[ChunkMetadata]) -> IndexSummary:
        summary = self._index_manager.index_course(course_id, chunks)
        self._corpus_versions[course_id] = summary.corpus_version
        return summary

    def index_chunks(self, course_id: str, chunks: list[ChunkMetadata]) -> IndexSummary:
        """把新导入的课程资料增量写入向量库，使其可以立即被检索和引用。"""
        summary = self._index_manager.index_chunks(course_id, chunks)
        self._corpus_versions[course_id] = summary.corpus_version
        return summary

    def answer(
        self,
        question: str,
        scope: RetrievalScope,
        options: RagExecutionOptions | None = None,
    ) -> RagResult:
        top_k = options.top_k if options and options.top_k is not None else self._top_k
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10")
        self._validate_requested_components(options)
        outcome = self._retrieval.retrieve(
            RetrievalQuery(
                question=question,
                scope=scope,
                top_k=top_k,
                fetch_k=max(self._fetch_k, top_k),
            )
        )
        if not outcome.chunks:
            return self._refusal(scope, outcome, top_k, "insufficient-evidence")

        generation_start = perf_counter()
        try:
            draft = self._generator.generate(question, list(outcome.chunks))
        except Exception:
            if not self._allow_degraded or self._fallback_generator is None:
                raise
            draft = replace(
                self._fallback_generator.generate(question, list(outcome.chunks)),
                degraded=True,
            )
        generation_ms = (perf_counter() - generation_start) * 1000
        assembled = self._citation_assembler.assemble(draft, outcome.chunks)
        if not assembled.answer or not assembled.citations:
            return self._refusal(scope, outcome, top_k, draft.resolved_model)

        confidence = sum(
            min(1, max(0, item.final_score)) for item in outcome.chunks
        ) / len(outcome.chunks)
        reranker_degraded = (
            self._retrieval.reranker_id != "disabled" and not outcome.reranker_applied
        )
        return RagResult(
            answer=assembled.answer,
            citations=assembled.citations,
            confidence=confidence,
            degraded=draft.degraded or reranker_degraded,
            runtime=self._runtime(
                scope,
                top_k,
                outcome,
                draft.resolved_model,
                generation_ms,
            ),
        )

    def _refusal(
        self,
        scope: RetrievalScope,
        outcome: RetrievalOutcome,
        top_k: int,
        model: str,
    ) -> RagResult:
        return RagResult(
            answer="课程资料中没有足够证据回答该问题。",
            citations=(),
            confidence=0,
            degraded=True,
            runtime=self._runtime(scope, top_k, outcome, model, 0),
        )

    def _runtime(
        self,
        scope: RetrievalScope,
        top_k: int,
        outcome: RetrievalOutcome,
        model: str,
        generation_ms: float,
    ) -> RagRuntime:
        return RagRuntime(
            mode=self._mode,
            embedding=self._retrieval.embedding_id,
            vector_store=self._retrieval.vector_store_id,
            reranker=(
                self._retrieval.reranker_id
                if outcome.reranker_applied
                else "disabled-or-degraded"
            ),
            model=model,
            top_k=top_k,
            fetch_k=max(self._fetch_k, top_k),
            retrieval_ms=outcome.retrieval_ms,
            rerank_ms=outcome.rerank_ms,
            generation_ms=generation_ms,
            corpus_version=self._corpus_versions.get(scope.course_id, "unindexed"),
        )

    def _validate_requested_components(
        self, options: RagExecutionOptions | None
    ) -> None:
        if not options:
            return
        requested = {
            "embedding": (options.embedding, self._retrieval.embedding_id),
            "reranker": (options.reranker, self._retrieval.reranker_id),
            "model": (options.model, self._generator.model_id),
        }
        for component, (value, resolved) in requested.items():
            if value is not None and value != resolved:
                raise ValueError(
                    f"requested {component} {value!r} is unavailable; resolved {resolved!r}"
                )

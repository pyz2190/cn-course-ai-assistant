from dataclasses import asdict, dataclass
from typing import Protocol

from app.domain.rag import RagExecutionOptions, RetrievalScope
from app.services.rag import RagService


class EvaluationRequest(Protocol):
    question: str
    knowledge_point_ids: list[str]


class EvaluationRuntime(Protocol):
    model: str | None
    embedding: str | None
    reranker: str | None
    top_k: int | None


@dataclass(frozen=True)
class EvaluationAdapterResult:
    generated_answer: str
    citations: list[dict[str, object]]
    runtime: dict[str, object]


class InProcessRagAdapter:
    """C-to-D adapter with a deliberately sanitized input surface."""

    def __init__(self, rag_service: RagService, course_id: str = "computer-networks") -> None:
        self._rag_service = rag_service
        self._course_id = course_id

    def answer(
        self,
        item: EvaluationRequest,
        runtime: EvaluationRuntime,
    ) -> EvaluationAdapterResult:
        result = self._rag_service.answer(
            item.question,
            RetrievalScope(
                course_id=self._course_id,
                knowledge_point_ids=tuple(item.knowledge_point_ids),
            ),
            RagExecutionOptions(
                model=runtime.model,
                embedding=runtime.embedding,
                reranker=runtime.reranker,
                top_k=runtime.top_k,
            ),
        )
        return EvaluationAdapterResult(
            generated_answer=result.answer,
            citations=[
                citation.model_dump(mode="json") for citation in result.citations
            ],
            runtime=asdict(result.runtime),
        )

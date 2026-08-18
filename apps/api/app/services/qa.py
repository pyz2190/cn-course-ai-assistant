from uuid import uuid4

from app.domain.models import AskRequest, AskResponse
from app.domain.rag import RetrievalScope
from app.services.rag import RagService


class QaService:
    def __init__(self, rag_service: RagService) -> None:
        self._rag_service = rag_service

    def ask(self, request: AskRequest) -> AskResponse:
        result = self._rag_service.answer(
            request.question,
            RetrievalScope(
                course_id=request.course_id,
                knowledge_point_ids=tuple(request.knowledge_point_ids),
                resource_ids=tuple(request.resource_ids),
                task_id=request.task_id,
            ),
        )
        return AskResponse(
            answer=result.answer,
            citations=list(result.citations),
            confidence=result.confidence,
            request_id=f"req-{uuid4().hex}",
            degraded=result.degraded,
            mode=result.runtime.mode,
        )

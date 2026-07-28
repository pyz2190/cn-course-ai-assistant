from app.domain.models import AskRequest, AskResponse
from app.services.ports import AnswerGenerator, Retriever


class QaService:
    def __init__(self, retriever: Retriever, answer_generator: AnswerGenerator) -> None:
        self._retriever = retriever
        self._answer_generator = answer_generator

    def ask(self, request: AskRequest) -> AskResponse:
        chunks = self._retriever.retrieve(request.question, request.course_id)
        return self._answer_generator.generate(request.question, chunks)

from dataclasses import dataclass

from scripts.evaluate import RagRequest, RuntimeParameters

from app.adapters.evaluation import InProcessRagAdapter
from app.domain.rag import RagResult, RagRuntime


class CapturingRagService:
    def __init__(self) -> None:
        self.call = None

    def answer(self, question, scope, options):
        self.call = (question, scope, options)
        return RagResult(
            answer="资料不足。",
            citations=(),
            confidence=0,
            degraded=True,
            runtime=RagRuntime(
                mode="offline",
                embedding="offline-hash-v1-384d",
                vector_store="qdrant:test",
                reranker="offline-overlap-v1",
                model="offline-extractive-v1",
                top_k=3,
                fetch_k=8,
                retrieval_ms=1,
                rerank_ms=1,
                generation_ms=1,
                corpus_version="corpus-test",
            ),
        )


def test_adapter_forwards_only_sanitized_fields_and_runtime_options() -> None:
    service = CapturingRagService()
    adapter = InProcessRagAdapter(service)  # type: ignore[arg-type]
    request = RagRequest(
        evaluation_id="QA-PROTOCOL-001",
        question="TCP 为什么需要三次握手？",
        knowledge_point_ids=["kp-transport-tcp-handshake"],
    )
    runtime = RuntimeParameters(
        model=None,
        embedding=None,
        reranker=None,
        top_k=3,
        git_commit="abc123",
    )

    response = adapter.answer(request, runtime)

    question, scope, options = service.call
    assert question == request.question
    assert scope.knowledge_point_ids == ("kp-transport-tcp-handshake",)
    assert options.top_k == 3
    assert "expected_answer" not in repr(service.call)
    assert "key_points" not in repr(service.call)
    assert response.runtime["corpus_version"] == "corpus-test"


@dataclass(frozen=True)
class LeakyLookingRequest:
    question: str
    knowledge_point_ids: list[str]
    expected_answer: str
    key_points: list[str]


def test_adapter_contract_cannot_read_evaluation_answers() -> None:
    service = CapturingRagService()
    adapter = InProcessRagAdapter(service)  # type: ignore[arg-type]
    request = LeakyLookingRequest(
        question="DNS 是什么？",
        knowledge_point_ids=["kp-application-dns"],
        expected_answer="secret expected answer",
        key_points=["secret annotation point"],
    )
    runtime = RuntimeParameters(None, None, None, None, None)

    adapter.answer(request, runtime)

    assert "secret expected answer" not in repr(service.call)
    assert "secret annotation point" not in repr(service.call)

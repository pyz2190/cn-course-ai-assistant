import json

import httpx2
import pytest

from app.adapters.mock import MOCK_CHUNKS
from app.adapters.rag.generators import (
    OfflineExtractiveGenerator,
    OpenAICompatibleGenerator,
)
from app.domain.rag import (
    GenerationDraft,
    GroundedSentence,
    RetrievedChunk,
)
from app.services.rag import CitationAssembler


def _evidence() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk=MOCK_CHUNKS[3],
            retrieval_score=0.8,
            rerank_score=0.9,
            final_score=0.9,
        )
    ]


def test_offline_generator_uses_only_known_evidence_id() -> None:
    draft = OfflineExtractiveGenerator().generate("TCP 为什么三次握手？", _evidence())

    assert draft.sentences
    assert all(
        sentence.evidence_ids == ("chunk-transport-tcp-001",)
        for sentence in draft.sentences
    )
    assert all(sentence.text in MOCK_CHUNKS[3].content for sentence in draft.sentences)


def test_citation_assembler_adds_stable_sentence_markers() -> None:
    draft = GenerationDraft(
        sentences=(
            GroundedSentence("第一句。", (MOCK_CHUNKS[3].chunk_id,)),
            GroundedSentence("第二句。", (MOCK_CHUNKS[3].chunk_id,)),
        ),
        resolved_model="test",
        degraded=False,
    )

    result = CitationAssembler().assemble(draft, tuple(_evidence()))

    assert result.answer == "第一句。[1]第二句。[1]"
    assert len(result.citations) == 1
    assert result.citations[0].page_start == 214
    assert result.citations[0].retrieval_score == 0.8


def test_citation_assembler_drops_fabricated_evidence() -> None:
    draft = GenerationDraft(
        sentences=(GroundedSentence("虚构事实。", ("missing-chunk",)),),
        resolved_model="test",
        degraded=False,
    )

    result = CitationAssembler().assemble(draft, tuple(_evidence()))

    assert result.answer == ""
    assert result.citations == ()


def test_external_generator_uses_sanitized_grounded_request() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured["body"] = json.loads(request.content)
        captured["authorization"] = request.headers.get("Authorization")
        content = json.dumps(
            {
                "sentences": [
                    {
                        "text": "TCP 握手同步初始序列号。",
                        "evidence_ids": ["chunk-transport-tcp-001"],
                    }
                ]
            },
            ensure_ascii=False,
        )
        return httpx2.Response(
            200,
            json={
                "model": "test-model-2026",
                "choices": [{"message": {"content": content}}],
            },
        )

    client = httpx2.Client(transport=httpx2.MockTransport(handler))
    generator = OpenAICompatibleGenerator(
        base_url="https://model.example/v1",
        model_id="test-model",
        api_key="secret-test-value",
        timeout=httpx2.Timeout(5),
        max_retries=0,
        client=client,
    )

    result = generator.generate("TCP 为什么三次握手？", _evidence())

    body = json.dumps(captured["body"], ensure_ascii=False)
    assert "student-demo" not in body
    assert "expected_answer" not in body
    assert "secret-test-value" not in body
    assert captured["authorization"] == "Bearer secret-test-value"
    assert result.resolved_model == "test-model-2026"
    assert result.sentences[0].evidence_ids == ("chunk-transport-tcp-001",)


def test_external_generator_retries_timeout_once() -> None:
    attempts = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1
        raise httpx2.ReadTimeout("timed out", request=request)

    generator = OpenAICompatibleGenerator(
        base_url="https://model.example/v1",
        model_id="test-model",
        api_key=None,
        timeout=httpx2.Timeout(1),
        max_retries=1,
        client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )

    with pytest.raises(httpx2.ReadTimeout):
        generator.generate("TCP", _evidence())
    assert attempts == 2

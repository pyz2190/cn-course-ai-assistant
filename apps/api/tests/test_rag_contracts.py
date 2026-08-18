from dataclasses import FrozenInstanceError

import pytest

from app.domain.models import AskRequest, AskResponse, Citation
from app.domain.rag import RetrievalScope


def test_legacy_ask_request_remains_valid() -> None:
    request = AskRequest(
        course_id="computer-networks",
        user_id="student-demo",
        question="TCP 为什么需要三次握手？",
    )

    assert request.knowledge_point_ids == []
    assert request.resource_ids == []
    assert request.task_id is None


def test_ask_request_accepts_optional_retrieval_scope() -> None:
    request = AskRequest(
        course_id="computer-networks",
        user_id="student-demo",
        question="分析实验抓包",
        knowledge_point_ids=["kp-transport-tcp-handshake"],
        resource_ids=["resource-001"],
        task_id="task-protocol-tcp-handshake",
    )

    assert request.task_id == "task-protocol-tcp-handshake"
    assert request.resource_ids == ["resource-001"]


def test_safe_refusal_can_have_no_citations() -> None:
    response = AskResponse(
        answer="课程资料中没有足够证据回答该问题。",
        citations=[],
        confidence=0,
        request_id="req-test",
        degraded=True,
    )

    assert response.citations == []
    assert response.mode == "offline"


def test_citation_accepts_retrieval_and_rerank_scores() -> None:
    citation = Citation(
        citation_id="citation-1",
        chunk_id="chunk-1",
        resource_id="resource-1",
        title="课程资料",
        chapter="第 1 章",
        quote="证据内容",
        retrieval_score=0.8,
        rerank_score=2.1,
    )

    assert citation.retrieval_score == 0.8
    assert citation.rerank_score == 2.1


def test_retrieval_scope_is_immutable() -> None:
    scope = RetrievalScope(course_id="computer-networks")

    with pytest.raises(FrozenInstanceError):
        scope.course_id = "other"  # type: ignore[misc]

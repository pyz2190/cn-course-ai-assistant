from datetime import UTC, datetime

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["mode"] == "mock"
    assert response.headers["X-Request-ID"].startswith("req-")


def test_import_resource_returns_metadata(client: TestClient) -> None:
    response = client.post(
        "/api/v1/resources/import",
        json={
            "course_id": "computer-networks",
            "resource_type": "slide",
            "title": "运输层课件",
            "version": "v1",
            "language": "zh",
            "content_type": "ppt",
            "source_url": None,
        },
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["sync_status"] == "completed"
    assert payload["metadata"]["resource_id"] == payload["resource_id"]
    assert payload["metadata"]["chapter"] == "待人工审核"


def test_ask_returns_traceable_citation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/qa/ask",
        json={
            "course_id": "computer-networks",
            "user_id": "student-demo",
            "question": "TCP 为什么需要三次握手？",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence"] == 0.92
    assert payload["citations"][0]["chapter"] == "第 3 章 运输层"
    assert payload["citations"][0]["page_start"] == 214


def test_empty_question_uses_stable_error_shape(client: TestClient) -> None:
    response = client.post(
        "/api/v1/qa/ask",
        json={
            "course_id": "computer-networks",
            "user_id": "student-demo",
            "question": "",
        },
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["request_id"].startswith("req-")


def test_tasks_cover_six_types(client: TestClient) -> None:
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 6
    assert {item["task_type"] for item in payload} == {
        "foundation",
        "protocol_analysis",
        "case_study",
        "innovation_challenge",
        "project_practice",
        "troubleshooting",
    }


def test_task_detail_and_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/tasks/task-protocol-tcp-handshake")
    assert response.status_code == 200
    assert response.json()["ai_feedback_points"]

    missing = client.get("/api/v1/tasks/not-found")
    assert missing.status_code == 404
    assert missing.json()["code"] == "http_404"


def test_record_learning_event(client: TestClient) -> None:
    occurred_at = datetime(2026, 7, 28, tzinfo=UTC).isoformat()
    response = client.post(
        "/api/v1/events",
        json={
            "event_id": "event-demo-001",
            "course_id": "computer-networks",
            "user_id": "student-demo",
            "event_type": "task_opened",
            "object_id": "task-protocol-tcp-handshake",
            "occurred_at": occurred_at,
            "payload": {"source": "web-demo"},
        },
    )
    assert response.status_code == 201
    assert response.json()["event_id"] == "event-demo-001"

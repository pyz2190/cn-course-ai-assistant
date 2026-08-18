from fastapi.testclient import TestClient


def feedback_payload(*, request_id: str = "req-feedback-1") -> dict:
    return {
        "course_id": "computer-networks",
        "user_id": "student-demo",
        "request_id": request_id,
        "question": "TCP 为什么需要三次握手？",
        "answer": "因为需要建立连接。",
        "reason": "回答没有说明双向通信能力和初始序列号。",
        "citation_ids": ["citation-1"],
    }


def create_feedback(client: TestClient, *, request_id: str = "req-feedback-1") -> dict:
    response = client.post("/api/v1/feedback", json=feedback_payload(request_id=request_id))
    assert response.status_code == 201
    return response.json()


def test_create_and_filter_pending_feedback(client: TestClient) -> None:
    created = create_feedback(client)

    assert created["feedback_id"].startswith("feedback-")
    assert created["status"] == "pending_review"
    assert created["reviewer"] is None

    response = client.get(
        "/api/v1/feedback",
        params={
            "course_id": "computer-networks",
            "user_id": "student-demo",
            "request_id": "req-feedback-1",
            "status": "pending_review",
        },
    )
    assert response.status_code == 200
    assert [item["feedback_id"] for item in response.json()] == [created["feedback_id"]]


def test_approve_feedback_creates_structured_change_task(client: TestClient) -> None:
    created = create_feedback(client)

    response = client.patch(
        f"/api/v1/feedback/{created['feedback_id']}/review",
        json={
            "decision": "approved",
            "reviewer": "teacher-demo",
            "review_notes": "确认答案遗漏关键解释。",
            "suggested_action": "补充三次握手对初始序列号与双向能力的说明。",
        },
    )

    assert response.status_code == 200
    reviewed = response.json()
    assert reviewed["status"] == "approved"
    assert reviewed["reviewer"] == "teacher-demo"
    assert reviewed["knowledge_base_change_id"].startswith("kb-change-")

    change = client.get(f"/api/v1/knowledge-base/changes/{reviewed['knowledge_base_change_id']}")
    assert change.status_code == 200
    assert change.json() == {
        "change_id": reviewed["knowledge_base_change_id"],
        "feedback_id": created["feedback_id"],
        "course_id": "computer-networks",
        "request_id": "req-feedback-1",
        "question": "TCP 为什么需要三次握手？",
        "reason": "回答没有说明双向通信能力和初始序列号。",
        "suggested_action": "补充三次握手对初始序列号与双向能力的说明。",
        "status": "pending",
        "created_at": change.json()["created_at"],
    }

    filtered = client.get(
        "/api/v1/knowledge-base/changes",
        params={"course_id": "computer-networks", "feedback_id": created["feedback_id"]},
    )
    assert [item["change_id"] for item in filtered.json()] == [reviewed["knowledge_base_change_id"]]


def test_reject_feedback_without_change_and_prevent_second_review(client: TestClient) -> None:
    created = create_feedback(client, request_id="req-feedback-reject")
    review_url = f"/api/v1/feedback/{created['feedback_id']}/review"

    rejected = client.patch(
        review_url,
        json={
            "decision": "rejected",
            "reviewer": "ta-demo",
            "review_notes": "答案有效，不进入知识库优化。",
        },
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["knowledge_base_change_id"] is None

    duplicate = client.patch(
        review_url,
        json={
            "decision": "rejected",
            "reviewer": "ta-demo",
            "review_notes": "再次审核。",
        },
    )
    assert duplicate.status_code == 409

    changes = client.get(
        "/api/v1/knowledge-base/changes",
        params={"feedback_id": created["feedback_id"]},
    )
    assert changes.json() == []


def test_approval_requires_suggested_action_and_missing_records_are_404(
    client: TestClient,
) -> None:
    created = create_feedback(client, request_id="req-feedback-invalid-review")
    invalid = client.patch(
        f"/api/v1/feedback/{created['feedback_id']}/review",
        json={"decision": "approved", "reviewer": "teacher-demo"},
    )
    assert invalid.status_code == 422

    assert client.get("/api/v1/feedback/not-found").status_code == 404
    assert client.get("/api/v1/knowledge-base/changes/not-found").status_code == 404

"""知识库变更任务必须能被推进和关闭，否则“持续优化知识库”只有开头没有结尾。"""

from fastapi.testclient import TestClient


def _approved_change(client: TestClient, request_id: str = "req-kb-1") -> dict:
    created = client.post(
        "/api/v1/feedback",
        json={
            "course_id": "computer-networks",
            "user_id": "student-demo",
            "request_id": request_id,
            "question": "TCP 为什么需要三次握手？",
            "answer": "三次握手用于建立连接。",
            "reason": "回答没有说明初始序列号同步。",
            "citation_ids": [],
        },
    ).json()
    reviewed = client.patch(
        f"/api/v1/feedback/{created['feedback_id']}/review",
        json={
            "decision": "approved",
            "reviewer": "teacher-demo",
            "review_notes": "确认语料缺口。",
            "suggested_action": "补充初始序列号同步的说明。",
        },
    ).json()
    return client.get(
        f"/api/v1/knowledge-base/changes/{reviewed['knowledge_base_change_id']}"
    ).json()


def test_change_task_can_be_taken_and_completed(client: TestClient) -> None:
    change = _approved_change(client)
    assert change["status"] == "pending"
    assert change["handler"] is None

    taken = client.patch(
        f"/api/v1/knowledge-base/changes/{change['change_id']}",
        json={"status": "in_progress", "handler": "ta-zhang"},
    )
    assert taken.status_code == 200
    assert taken.json()["status"] == "in_progress"
    assert taken.json()["handler"] == "ta-zhang"
    assert taken.json()["updated_at"] is not None

    done = client.patch(
        f"/api/v1/knowledge-base/changes/{change['change_id']}",
        json={
            "status": "done",
            "handler": "ta-zhang",
            "resolution_notes": "已补充握手序列号切片。",
            "resource_ids": ["resource-cn-textbook-001"],
        },
    )
    assert done.status_code == 200
    payload = done.json()
    assert payload["status"] == "done"
    assert payload["resource_ids"] == ["resource-cn-textbook-001"]
    assert payload["resolution_notes"] == "已补充握手序列号切片。"


def test_pending_queue_shrinks_once_a_change_is_closed(client: TestClient) -> None:
    keep = _approved_change(client, "req-keep")
    close = _approved_change(client, "req-close")

    client.patch(
        f"/api/v1/knowledge-base/changes/{close['change_id']}",
        json={
            "status": "wont_fix",
            "handler": "teacher-li",
            "resolution_notes": "问题源于提问超出课程范围。",
        },
    )

    pending = client.get("/api/v1/knowledge-base/changes", params={"change_status": "pending"})
    assert [item["change_id"] for item in pending.json()] == [keep["change_id"]]


def test_closed_change_cannot_be_reopened(client: TestClient) -> None:
    change = _approved_change(client)
    client.patch(
        f"/api/v1/knowledge-base/changes/{change['change_id']}",
        json={"status": "done", "handler": "ta-zhang", "resolution_notes": "已完成。"},
    )

    again = client.patch(
        f"/api/v1/knowledge-base/changes/{change['change_id']}",
        json={"status": "in_progress", "handler": "ta-zhang"},
    )
    assert again.status_code == 409


def test_wont_fix_requires_resolution_notes(client: TestClient) -> None:
    change = _approved_change(client)
    response = client.patch(
        f"/api/v1/knowledge-base/changes/{change['change_id']}",
        json={"status": "wont_fix", "handler": "teacher-li"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_update_cannot_move_change_back_to_pending(client: TestClient) -> None:
    change = _approved_change(client)
    response = client.patch(
        f"/api/v1/knowledge-base/changes/{change['change_id']}",
        json={"status": "pending", "handler": "ta-zhang"},
    )
    assert response.status_code == 422


def test_updating_unknown_change_returns_not_found(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/knowledge-base/changes/kb-change-missing",
        json={"status": "in_progress", "handler": "ta-zhang"},
    )
    assert response.status_code == 404

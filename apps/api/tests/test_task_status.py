"""任务需要能先存草稿再发布，否则 TaskStatus 的 draft 与 completed 永远用不到。"""

from fastapi.testclient import TestClient


def _payload(task_id: str, **overrides: object) -> dict:
    payload = {
        "task_id": task_id,
        "title": "子网划分练习",
        "description": "根据主机数量需求划分子网并给出地址规划。",
        "task_type": "foundation",
        "knowledge_point_ids": ["kp-network-addressing"],
        "resource_ids": ["resource-cn-textbook-001"],
        "completion_criteria": ["提交子网划分表并说明掩码选择理由。"],
        "ai_feedback_points": ["提交地址规划后检查地址冲突。"],
    }
    payload.update(overrides)
    return payload


def test_task_defaults_to_published(client: TestClient) -> None:
    response = client.post("/api/v1/tasks", json=_payload("task-default-status"))
    assert response.status_code == 201
    assert response.json()["status"] == "published"


def test_task_can_be_created_as_draft_then_published(client: TestClient) -> None:
    created = client.post("/api/v1/tasks", json=_payload("task-draft-flow", status="draft"))
    assert created.status_code == 201
    assert created.json()["status"] == "draft"

    drafts = client.get("/api/v1/tasks", params={"status": "draft"})
    assert "task-draft-flow" in {task["task_id"] for task in drafts.json()}

    published = client.patch("/api/v1/tasks/task-draft-flow/status", json={"status": "published"})
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    drafts_after = client.get("/api/v1/tasks", params={"status": "draft"})
    assert "task-draft-flow" not in {task["task_id"] for task in drafts_after.json()}


def test_task_can_be_marked_completed(client: TestClient) -> None:
    client.post("/api/v1/tasks", json=_payload("task-complete-flow"))
    response = client.patch("/api/v1/tasks/task-complete-flow/status", json={"status": "completed"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_task_list_filters_by_type(client: TestClient) -> None:
    response = client.get("/api/v1/tasks", params={"task_type": "troubleshooting"})
    assert response.status_code == 200
    assert {task["task_type"] for task in response.json()} == {"troubleshooting"}


def test_status_update_on_unknown_task_returns_not_found(client: TestClient) -> None:
    response = client.patch("/api/v1/tasks/task-missing/status", json={"status": "published"})
    assert response.status_code == 404


def test_unknown_status_is_rejected(client: TestClient) -> None:
    client.post("/api/v1/tasks", json=_payload("task-bad-status"))
    response = client.patch("/api/v1/tasks/task-bad-status/status", json={"status": "archived"})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"

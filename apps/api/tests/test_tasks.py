from fastapi.testclient import TestClient


def task_payload() -> dict:
    return {
        "task_id": "task-published-by-api",
        "title": "分析 HTTP 缓存行为",
        "description": "通过请求与响应首部判断缓存是否命中。",
        "task_type": "protocol_analysis",
        "knowledge_point_ids": ["kp-application-http"],
        "resource_ids": ["resource-cn-textbook-001"],
        "prerequisite_ids": [],
        "completion_criteria": ["正确解释 Cache-Control。"],
        "ai_feedback_points": ["检查首部字段解释。"],
    }


def test_publish_task_and_query_it(client: TestClient) -> None:
    response = client.post("/api/v1/tasks", json=task_payload())

    assert response.status_code == 201
    assert response.json()["status"] == "published"

    detail = client.get("/api/v1/tasks/task-published-by-api")
    assert detail.status_code == 200
    assert detail.json()["title"] == "分析 HTTP 缓存行为"

    listed = client.get("/api/v1/tasks")
    assert any(task["task_id"] == "task-published-by-api" for task in listed.json())


def test_duplicate_task_id_does_not_overwrite_existing_task(client: TestClient) -> None:
    original = task_payload()
    assert client.post("/api/v1/tasks", json=original).status_code == 201

    duplicate = {**original, "title": "不应覆盖的标题"}
    response = client.post("/api/v1/tasks", json=duplicate)

    assert response.status_code == 409
    detail = client.get("/api/v1/tasks/task-published-by-api")
    assert detail.json()["title"] == original["title"]

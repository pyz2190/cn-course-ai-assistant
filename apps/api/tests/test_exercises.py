"""试题接口与「任务 → 知识点 → 资料 → 试题」关联链的测试。"""

from fastapi.testclient import TestClient

from app.adapters.exercises import COURSE_EXERCISES
from app.adapters.mock import MOCK_TASKS


def test_list_exercises_returns_course_bank(client: TestClient) -> None:
    response = client.get("/api/v1/exercises")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(COURSE_EXERCISES)
    assert {item["exercise_id"] for item in body} == {
        exercise.exercise_id for exercise in COURSE_EXERCISES
    }


def test_list_exercises_filters_by_knowledge_point(client: TestClient) -> None:
    response = client.get(
        "/api/v1/exercises", params={"knowledge_point_id": "kp-network-addressing"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body
    for item in body:
        assert "kp-network-addressing" in item["knowledge_point_ids"]


def test_list_exercises_by_task_returns_linked_exercises(client: TestClient) -> None:
    response = client.get("/api/v1/exercises", params={"task_id": "task-foundation-addressing"})

    assert response.status_code == 200
    assert [item["exercise_id"] for item in response.json()] == ["ex-network-addressing-001"]


def test_list_exercises_for_unknown_task_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/exercises", params={"task_id": "task-does-not-exist"})

    assert response.status_code == 404
    assert response.json()["code"]


def test_get_exercise_detail(client: TestClient) -> None:
    response = client.get("/api/v1/exercises/ex-network-addressing-001")

    assert response.status_code == 200
    body = response.json()
    assert body["exercise_type"] == "single_choice"
    assert len(body["options"]) >= 2
    assert body["reference_answer"]
    assert body["resource_ids"] == ["resource-cn-textbook-001"]


def test_get_unknown_exercise_returns_error_contract(client: TestClient) -> None:
    response = client.get("/api/v1/exercises/ex-missing")

    assert response.status_code == 404
    body = response.json()
    assert body["code"]
    assert body["message"]
    assert body["request_id"]


def test_every_mock_task_links_to_a_resolvable_exercise(client: TestClient) -> None:
    """任务的 exercise_ids 必须能在试题库中解析，否则任务的完成判据不可判定。"""
    known = {exercise.exercise_id for exercise in COURSE_EXERCISES}

    for task in MOCK_TASKS:
        assert task.exercise_ids, f"{task.task_id} 未关联试题"
        for exercise_id in task.exercise_ids:
            assert exercise_id in known, f"{task.task_id} 关联了不存在的试题 {exercise_id}"


def test_task_exercise_shares_knowledge_point_with_task(client: TestClient) -> None:
    """任务与其试题必须落在同一知识点上，保证试题确实检验该任务的目标。"""
    exercises = {exercise.exercise_id: exercise for exercise in COURSE_EXERCISES}

    for task in MOCK_TASKS:
        for exercise_id in task.exercise_ids:
            shared = set(exercises[exercise_id].knowledge_point_ids) & set(
                task.knowledge_point_ids
            )
            assert shared, f"{task.task_id} 与 {exercise_id} 没有共同知识点"

"""知识点接口让任务、Chunk 和评测集里的 knowledge_point_ids 可以解析为知识图谱节点。"""

from fastapi.testclient import TestClient

from app.adapters.knowledge_points import COURSE_KNOWLEDGE_POINTS
from app.adapters.mock import MOCK_CHUNKS, MOCK_TASKS


def test_list_returns_the_course_knowledge_graph(client: TestClient) -> None:
    response = client.get("/api/v1/knowledge-points")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == len(COURSE_KNOWLEDGE_POINTS)
    assert {item["knowledge_point_id"] for item in payload} == {
        item.knowledge_point_id for item in COURSE_KNOWLEDGE_POINTS
    }


def test_knowledge_point_detail_carries_graph_edges(client: TestClient) -> None:
    response = client.get("/api/v1/knowledge-points/kp-transport-congestion-control")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "TCP 拥塞控制"
    assert payload["chapter"] == "第 3 章 运输层"
    assert payload["prerequisite_ids"] == ["kp-transport-tcp-handshake"]
    assert payload["keywords_en"]
    assert payload["keywords_zh"]


def test_knowledge_points_filter_by_chapter(client: TestClient) -> None:
    response = client.get("/api/v1/knowledge-points", params={"chapter": "第 3 章 运输层"})
    assert {item["knowledge_point_id"] for item in response.json()} == {
        "kp-transport-udp",
        "kp-transport-tcp-handshake",
        "kp-transport-congestion-control",
    }


def test_unknown_knowledge_point_returns_not_found(client: TestClient) -> None:
    assert client.get("/api/v1/knowledge-points/kp-does-not-exist").status_code == 404


def test_every_task_knowledge_point_resolves(client: TestClient) -> None:
    known = {item.knowledge_point_id for item in COURSE_KNOWLEDGE_POINTS}
    referenced = {kp_id for task in MOCK_TASKS for kp_id in task.knowledge_point_ids}
    assert referenced <= known


def test_every_chunk_knowledge_point_resolves(client: TestClient) -> None:
    known = {item.knowledge_point_id for item in COURSE_KNOWLEDGE_POINTS}
    referenced = {kp_id for chunk in MOCK_CHUNKS for kp_id in chunk.knowledge_point_ids}
    assert referenced <= known


def test_prerequisites_and_parents_point_at_existing_nodes(client: TestClient) -> None:
    known = {item.knowledge_point_id for item in COURSE_KNOWLEDGE_POINTS}
    for item in COURSE_KNOWLEDGE_POINTS:
        assert item.parent_id is None or item.parent_id in known
        assert set(item.prerequisite_ids) <= known
        assert item.knowledge_point_id not in item.prerequisite_ids

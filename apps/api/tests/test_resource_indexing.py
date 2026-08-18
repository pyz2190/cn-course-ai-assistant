"""导入的课程资料必须能被检索到，否则解析和入库都没有意义。"""

import io

from fastapi.testclient import TestClient

SUBTITLE = """1
00:00:01,000 --> 00:00:09,000
紫金港骨干网采用 VRRP 心跳间隔 3 秒，抢占延时 30 秒，避免链路抖动引起主备频繁切换。
"""

QUESTION = "紫金港骨干网的 VRRP 心跳间隔和抢占延时是多少？"


def _upload(client: TestClient, filename: str = "lecture.srt", title: str = "紫金港骨干网讲解"):
    return client.post(
        "/api/v1/resources/upload",
        files={"file": (filename, io.BytesIO(SUBTITLE.encode("utf-8")), "text/plain")},
        data={
            "course_id": "computer-networks",
            "title": title,
            "content_type": "subtitle",
            "language": "zh",
            "knowledge_point_ids": "kp-network-design",
        },
    )


def _ask(client: TestClient) -> dict:
    return client.post(
        "/api/v1/qa/ask",
        json={
            "course_id": "computer-networks",
            "user_id": "student-demo",
            "question": QUESTION,
        },
    ).json()


def test_uploaded_material_becomes_retrievable(client: TestClient) -> None:
    before = _ask(client)
    assert before["citations"] == []
    assert before["confidence"] == 0

    upload = _upload(client)
    assert upload.status_code == 201
    payload = upload.json()
    assert payload["parse_status"] == "parsed"
    assert payload["indexed_chunks"] >= payload["chunk_count"]

    after = _ask(client)
    assert after["confidence"] > 0
    assert [citation["resource_id"] for citation in after["citations"]] == [payload["resource_id"]]
    assert "VRRP" in after["answer"]


def test_upload_reports_growing_index_size(client: TestClient) -> None:
    first = _upload(client, "lecture-a.srt", "讲解 A").json()
    second = _upload(client, "lecture-b.srt", "讲解 B").json()
    assert second["indexed_chunks"] > first["indexed_chunks"]


def test_uploaded_resource_can_be_listed_and_read_back(client: TestClient) -> None:
    uploaded = _upload(client).json()
    resource_id = uploaded["resource_id"]

    resources = client.get("/api/v1/resources")
    assert resources.status_code == 200
    summary = next(item for item in resources.json() if item["resource_id"] == resource_id)
    assert summary["title"] == "紫金港骨干网讲解"
    assert summary["course_id"] == "computer-networks"
    assert summary["chunk_count"] == uploaded["chunk_count"]

    chunks = client.get(f"/api/v1/resources/{resource_id}/chunks")
    assert chunks.status_code == 200
    assert [chunk["chunk_id"] for chunk in chunks.json()] == [
        chunk["chunk_id"] for chunk in uploaded["chunks"]
    ]


def test_resource_list_filters_by_course(client: TestClient) -> None:
    _upload(client)
    assert client.get("/api/v1/resources", params={"course_id": "other-course"}).json() == []
    owned = client.get("/api/v1/resources", params={"course_id": "computer-networks"}).json()
    assert len(owned) == 1


def test_unknown_resource_chunks_return_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/resources/resource-missing/chunks")
    assert response.status_code == 404

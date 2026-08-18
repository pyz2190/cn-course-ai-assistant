"""质量审查系统测试。"""

from fastapi.testclient import TestClient


class TestQualityReviewAPI:
    """质量审查 API 测试。"""

    def test_create_review(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/quality/reviews",
            json={
                "chunk_id": "chunk-transport-tcp-001",
                "resource_id": "resource-000",
                "reviewer": "张三",
                "score": 4,
                "issues": ["页码略有偏差"],
                "notes": "内容准确，页码需校对",
            },
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["chunk_id"] == "chunk-transport-tcp-001"
        assert payload["reviewer"] == "张三"
        assert payload["score"] == 4
        assert payload["issues"] == ["页码略有偏差"]
        assert payload["review_id"].startswith("review-")

    def test_list_reviews(self, client: TestClient) -> None:
        # 创建两条审查记录
        client.post(
            "/api/v1/quality/reviews",
            json={
                "chunk_id": "chunk-001",
                "resource_id": "res-001",
                "reviewer": "A",
                "score": 5,
            },
        )
        client.post(
            "/api/v1/quality/reviews",
            json={
                "chunk_id": "chunk-002",
                "resource_id": "res-001",
                "reviewer": "B",
                "score": 3,
            },
        )
        response = client.get("/api/v1/quality/reviews")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_list_reviews_by_chunk(self, client: TestClient) -> None:
        client.post(
            "/api/v1/quality/reviews",
            json={
                "chunk_id": "chunk-filter-test",
                "resource_id": "res-001",
                "reviewer": "C",
                "score": 4,
            },
        )
        response = client.get("/api/v1/quality/reviews?chunk_id=chunk-filter-test")
        assert response.status_code == 200
        assert all(r["chunk_id"] == "chunk-filter-test" for r in response.json())

    def test_get_review_by_id(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/quality/reviews",
            json={
                "chunk_id": "chunk-get-test",
                "resource_id": "res-001",
                "reviewer": "D",
                "score": 2,
                "issues": ["内容缺失", "格式错误"],
            },
        )
        review_id = create_resp.json()["review_id"]
        response = client.get(f"/api/v1/quality/reviews/{review_id}")
        assert response.status_code == 200
        assert response.json()["score"] == 2
        assert len(response.json()["issues"]) == 2

    def test_get_review_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/quality/reviews/nonexistent")
        assert response.status_code == 404

    def test_review_score_range(self, client: TestClient) -> None:
        """分数必须在 1-5 之间。"""
        response = client.post(
            "/api/v1/quality/reviews",
            json={
                "chunk_id": "chunk-score-test",
                "resource_id": "res-001",
                "reviewer": "E",
                "score": 0,
            },
        )
        assert response.status_code == 422

        response = client.post(
            "/api/v1/quality/reviews",
            json={
                "chunk_id": "chunk-score-test",
                "resource_id": "res-001",
                "reviewer": "E",
                "score": 6,
            },
        )
        assert response.status_code == 422

    def test_review_valid_score_range(self, client: TestClient) -> None:
        """1-5 分都应该通过。"""
        for score in [1, 2, 3, 4, 5]:
            response = client.post(
                "/api/v1/quality/reviews",
                json={
                    "chunk_id": f"chunk-score-{score}",
                    "resource_id": "res-001",
                    "reviewer": "F",
                    "score": score,
                },
            )
            assert response.status_code == 201

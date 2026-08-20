from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def record_event(
    client: TestClient,
    *,
    event_id: str,
    event_type: str,
    object_id: str,
    course_id: str = "computer-networks",
    user_id: str = "student-demo",
    occurred_at: datetime,
) -> None:
    response = client.post(
        "/api/v1/events",
        json={
            "event_id": event_id,
            "course_id": course_id,
            "user_id": user_id,
            "event_type": event_type,
            "object_id": object_id,
            "occurred_at": occurred_at.isoformat(),
            "payload": {},
        },
    )
    assert response.status_code == 201


def test_query_events_without_filters_returns_stable_timeline(client: TestClient) -> None:
    base = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
    record_event(
        client,
        event_id="event-2",
        event_type="task_completed",
        object_id="task-1",
        occurred_at=base + timedelta(minutes=1),
    )
    record_event(
        client,
        event_id="event-b",
        event_type="qa_asked",
        object_id="request-1",
        occurred_at=base,
    )
    record_event(
        client,
        event_id="event-a",
        event_type="feedback_submitted",
        object_id="feedback-1",
        occurred_at=base,
    )

    response = client.get("/api/v1/events")

    assert response.status_code == 200
    assert [event["event_id"] for event in response.json()] == [
        "event-a",
        "event-b",
        "event-2",
    ]


def test_query_events_combines_all_filters_with_and(client: TestClient) -> None:
    occurred_at = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
    record_event(
        client,
        event_id="event-match",
        event_type="task_completed",
        object_id="task-1",
        occurred_at=occurred_at,
    )
    record_event(
        client,
        event_id="event-other-user",
        event_type="task_completed",
        object_id="task-1",
        user_id="student-other",
        occurred_at=occurred_at,
    )
    record_event(
        client,
        event_id="event-other-object",
        event_type="task_completed",
        object_id="task-2",
        occurred_at=occurred_at,
    )

    response = client.get(
        "/api/v1/events",
        params={
            "course_id": "computer-networks",
            "user_id": "student-demo",
            "event_type": "task_completed",
            "object_id": "task-1",
        },
    )

    assert response.status_code == 200
    assert [event["event_id"] for event in response.json()] == ["event-match"]

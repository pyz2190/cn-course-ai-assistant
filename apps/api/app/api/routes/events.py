from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_event_sink
from app.domain.enums import EventType
from app.domain.models import LearningEvent
from app.services.ports import EventSink

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[LearningEvent])
def query_events(
    sink: Annotated[EventSink, Depends(get_event_sink)],
    course_id: str | None = None,
    user_id: str | None = None,
    event_type: EventType | None = None,
    object_id: str | None = None,
) -> list[LearningEvent]:
    return sink.query(
        course_id=course_id,
        user_id=user_id,
        event_type=event_type,
        object_id=object_id,
    )


@router.post("", response_model=LearningEvent, status_code=status.HTTP_201_CREATED)
def record_event(
    event: LearningEvent,
    sink: Annotated[EventSink, Depends(get_event_sink)],
) -> LearningEvent:
    return sink.record(event)

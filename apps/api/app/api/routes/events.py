from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_event_sink
from app.domain.models import LearningEvent
from app.services.ports import EventSink

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=LearningEvent, status_code=status.HTTP_201_CREATED)
def record_event(
    event: LearningEvent,
    sink: Annotated[EventSink, Depends(get_event_sink)],
) -> LearningEvent:
    return sink.record(event)

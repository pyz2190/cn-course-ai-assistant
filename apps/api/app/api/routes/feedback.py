from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_feedback_store, get_knowledge_base_change_store
from app.domain.enums import FeedbackStatus, KnowledgeBaseChangeStatus
from app.domain.models import (
    AnswerFeedback,
    AnswerFeedbackCreate,
    FeedbackReviewRequest,
    KnowledgeBaseChangeTask,
)
from app.services.ports import FeedbackStore, KnowledgeBaseChangeStore

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=AnswerFeedback, status_code=status.HTTP_201_CREATED)
def create_feedback(
    request: AnswerFeedbackCreate,
    store: Annotated[FeedbackStore, Depends(get_feedback_store)],
) -> AnswerFeedback:
    feedback = AnswerFeedback(
        **request.model_dump(),
        feedback_id=f"feedback-{uuid4().hex}",
        status=FeedbackStatus.PENDING_REVIEW,
        created_at=datetime.now(UTC),
    )
    return store.create(feedback)


@router.get("", response_model=list[AnswerFeedback])
def list_feedback(
    store: Annotated[FeedbackStore, Depends(get_feedback_store)],
    course_id: str | None = None,
    user_id: str | None = None,
    request_id: str | None = None,
    feedback_status: Annotated[FeedbackStatus | None, Query(alias="status")] = None,
) -> list[AnswerFeedback]:
    feedback = store.list_all()
    if course_id is not None:
        feedback = [item for item in feedback if item.course_id == course_id]
    if user_id is not None:
        feedback = [item for item in feedback if item.user_id == user_id]
    if request_id is not None:
        feedback = [item for item in feedback if item.request_id == request_id]
    if feedback_status is not None:
        feedback = [item for item in feedback if item.status == feedback_status]
    return sorted(feedback, key=lambda item: (item.created_at, item.feedback_id))


@router.get("/{feedback_id}", response_model=AnswerFeedback)
def get_feedback(
    feedback_id: str,
    store: Annotated[FeedbackStore, Depends(get_feedback_store)],
) -> AnswerFeedback:
    feedback = store.get(feedback_id)
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到回答反馈。")
    return feedback


@router.patch("/{feedback_id}/review", response_model=AnswerFeedback)
def review_feedback(
    feedback_id: str,
    request: FeedbackReviewRequest,
    store: Annotated[FeedbackStore, Depends(get_feedback_store)],
    change_store: Annotated[KnowledgeBaseChangeStore, Depends(get_knowledge_base_change_store)],
) -> AnswerFeedback:
    feedback = store.get(feedback_id)
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到回答反馈。")
    if feedback.status != FeedbackStatus.PENDING_REVIEW:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该反馈已经审核。")

    reviewed_at = datetime.now(UTC)
    change_id: str | None = None
    if request.decision == "approved":
        change = KnowledgeBaseChangeTask(
            change_id=f"kb-change-{uuid4().hex}",
            feedback_id=feedback.feedback_id,
            course_id=feedback.course_id,
            request_id=feedback.request_id,
            question=feedback.question,
            reason=feedback.reason,
            suggested_action=request.suggested_action or "",
            status=KnowledgeBaseChangeStatus.PENDING,
            created_at=reviewed_at,
        )
        change_store.create(change)
        change_id = change.change_id

    reviewed = AnswerFeedback(
        **feedback.model_dump(
            exclude={
                "status",
                "reviewer",
                "reviewed_at",
                "review_notes",
                "knowledge_base_change_id",
            }
        ),
        status=FeedbackStatus(request.decision),
        reviewer=request.reviewer,
        reviewed_at=reviewed_at,
        review_notes=request.review_notes,
        knowledge_base_change_id=change_id,
    )
    return store.replace(reviewed)

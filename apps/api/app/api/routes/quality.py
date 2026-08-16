from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_quality_review_store
from app.domain.models import QualityReview, QualityReviewRequest
from app.services.ports import QualityReviewStore

router = APIRouter(prefix="/quality", tags=["quality"])


@router.post(
    "/reviews",
    response_model=QualityReview,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    request: QualityReviewRequest,
    store: Annotated[QualityReviewStore, Depends(get_quality_review_store)],
) -> QualityReview:
    """创建质量审查记录。"""
    review = QualityReview(
        review_id=f"review-{uuid4().hex[:12]}",
        chunk_id=request.chunk_id,
        resource_id=request.resource_id,
        reviewer=request.reviewer,
        score=request.score,
        issues=request.issues,
        notes=request.notes,
        reviewed_at=datetime.now(UTC),
    )
    return store.save(review)


@router.get(
    "/reviews",
    response_model=list[QualityReview],
)
def list_reviews(
    store: Annotated[QualityReviewStore, Depends(get_quality_review_store)],
    chunk_id: str | None = None,
) -> list[QualityReview]:
    """列出所有质量审查记录，可按 chunk_id 过滤。"""
    if chunk_id:
        return store.list_by_chunk(chunk_id)
    return store.list_all()


@router.get(
    "/reviews/{review_id}",
    response_model=QualityReview,
)
def get_review(
    review_id: str,
    store: Annotated[QualityReviewStore, Depends(get_quality_review_store)],
) -> QualityReview:
    """获取单条质量审查记录。"""
    review = store.get(review_id)
    if not review:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"审查记录不存在: {review_id}")
    return review

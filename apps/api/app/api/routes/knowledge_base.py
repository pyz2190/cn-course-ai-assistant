from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_knowledge_base_change_store
from app.domain.models import KnowledgeBaseChangeTask
from app.services.ports import KnowledgeBaseChangeStore

router = APIRouter(prefix="/knowledge-base/changes", tags=["knowledge-base"])


@router.get("", response_model=list[KnowledgeBaseChangeTask])
def list_changes(
    store: Annotated[KnowledgeBaseChangeStore, Depends(get_knowledge_base_change_store)],
    course_id: str | None = None,
    feedback_id: str | None = None,
) -> list[KnowledgeBaseChangeTask]:
    changes = store.list_all()
    if course_id is not None:
        changes = [change for change in changes if change.course_id == course_id]
    if feedback_id is not None:
        changes = [change for change in changes if change.feedback_id == feedback_id]
    return sorted(changes, key=lambda change: (change.created_at, change.change_id))


@router.get("/{change_id}", response_model=KnowledgeBaseChangeTask)
def get_change(
    change_id: str,
    store: Annotated[KnowledgeBaseChangeStore, Depends(get_knowledge_base_change_store)],
) -> KnowledgeBaseChangeTask:
    change = store.get(change_id)
    if change is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到知识库变更任务。",
        )
    return change

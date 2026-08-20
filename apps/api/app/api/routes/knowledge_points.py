from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_knowledge_point_repository
from app.domain.models import KnowledgePoint
from app.services.ports import KnowledgePointRepository

router = APIRouter(prefix="/knowledge-points", tags=["knowledge-points"])


@router.get("", response_model=list[KnowledgePoint])
def list_knowledge_points(
    repository: Annotated[KnowledgePointRepository, Depends(get_knowledge_point_repository)],
    chapter: Annotated[str | None, Query(description="按章节过滤")] = None,
    parent_id: Annotated[str | None, Query(description="按父知识点过滤")] = None,
) -> list[KnowledgePoint]:
    """列出课程知识点，支持按章节或父知识点浏览知识图谱。"""
    return repository.list_knowledge_points(chapter=chapter, parent_id=parent_id)


@router.get("/{knowledge_point_id}", response_model=KnowledgePoint)
def get_knowledge_point(
    knowledge_point_id: str,
    repository: Annotated[KnowledgePointRepository, Depends(get_knowledge_point_repository)],
) -> KnowledgePoint:
    knowledge_point = repository.get_knowledge_point(knowledge_point_id)
    if knowledge_point is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到知识点: {knowledge_point_id}",
        )
    return knowledge_point

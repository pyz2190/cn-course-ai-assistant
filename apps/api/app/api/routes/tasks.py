from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_task_repository
from app.domain.enums import TaskStatus
from app.domain.models import TaskPublishRequest, TaskTemplate
from app.services.ports import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskTemplate, status_code=status.HTTP_201_CREATED)
def publish_task(
    request: TaskPublishRequest,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskTemplate:
    task = TaskTemplate(**request.model_dump(), status=TaskStatus.PUBLISHED)
    try:
        return repository.create(task)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="任务 ID 已存在，未覆盖原任务。",
        ) from error


@router.get("", response_model=list[TaskTemplate])
def list_tasks(
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> list[TaskTemplate]:
    return repository.list_tasks()


@router.get("/{task_id}", response_model=TaskTemplate)
def get_task(
    task_id: str,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskTemplate:
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到教学任务。")
    return task

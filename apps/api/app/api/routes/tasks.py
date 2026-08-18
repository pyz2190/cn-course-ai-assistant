from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_task_repository
from app.domain.enums import TaskStatus, TaskType
from app.domain.models import TaskPublishRequest, TaskStatusUpdateRequest, TaskTemplate
from app.services.ports import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskTemplate, status_code=status.HTTP_201_CREATED)
def publish_task(
    request: TaskPublishRequest,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskTemplate:
    task = TaskTemplate(**request.model_dump())
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
    task_status: Annotated[
        TaskStatus | None, Query(alias="status", description="按任务状态过滤")
    ] = None,
    task_type: Annotated[TaskType | None, Query(description="按六类任务类型过滤")] = None,
) -> list[TaskTemplate]:
    return [
        task
        for task in repository.list_tasks()
        if (task_status is None or task.status == task_status)
        and (task_type is None or task.task_type == task_type)
    ]


@router.get("/{task_id}", response_model=TaskTemplate)
def get_task(
    task_id: str,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskTemplate:
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到教学任务。")
    return task


@router.patch("/{task_id}/status", response_model=TaskTemplate)
def update_task_status(
    task_id: str,
    request: TaskStatusUpdateRequest,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskTemplate:
    """在草稿、已发布和已完成之间流转任务状态。"""
    task = repository.update_status(task_id, request.status)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到教学任务。")
    return task

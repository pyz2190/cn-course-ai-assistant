from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_exercise_repository, get_task_repository
from app.domain.models import Exercise
from app.services.ports import ExerciseRepository, TaskRepository

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[Exercise])
def list_exercises(
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
    tasks: Annotated[TaskRepository, Depends(get_task_repository)],
    knowledge_point_id: Annotated[
        str | None, Query(description="按知识点过滤，用于沿知识图谱取题")
    ] = None,
    task_id: Annotated[
        str | None, Query(description="按任务过滤，返回该任务 exercise_ids 关联的试题")
    ] = None,
) -> list[Exercise]:
    """列出课程试题，可按知识点或任务取题。"""
    exercise_ids: list[str] | None = None
    if task_id is not None:
        task = tasks.get_task(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到教学任务: {task_id}",
            )
        exercise_ids = task.exercise_ids
        if not exercise_ids:
            return []
    return repository.list_exercises(
        knowledge_point_id=knowledge_point_id,
        exercise_ids=exercise_ids,
    )


@router.get("/{exercise_id}", response_model=Exercise)
def get_exercise(
    exercise_id: str,
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> Exercise:
    exercise = repository.get_exercise(exercise_id)
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到试题: {exercise_id}",
        )
    return exercise

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.viewsets.TaskViewSet import TaskViewSet
from app.viewsets.CommentViewSet import CommentViewSet
from app.viewsets.EvaluationViewSet import EvaluationViewSet
from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.evaluation import EvaluationCreate, EvaluationRead
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate


router = APIRouter(prefix="/tasks", tags=["Задачи"])


# -------------------------------------------------------------------
# Эндпоинты по задачам
# -------------------------------------------------------------------

@router.get("/", response_model=List[TaskRead])
async def list_tasks(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TaskViewSet(current_user, db)
    return await viewset.list_tasks()


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TaskViewSet(current_user, db)
    return await viewset.create_task(task_in)


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TaskViewSet(current_user, db)
    return await viewset.update_task(task_id, task_in)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TaskViewSet(current_user, db)
    await viewset.delete_task(task_id)


@router.post("/{task_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def add_comment(
    task_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = CommentViewSet(current_user, db)
    return await viewset.add_comment(task_id, comment_in)


@router.get("/{task_id}/comments", response_model=List[CommentRead])
async def list_comments(
    task_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = CommentViewSet(current_user, db)
    return await viewset.list_comments(task_id)


@router.post("/{task_id}/evaluations", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
async def add_evaluation(
    task_id: int,
    eval_in: EvaluationCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = EvaluationViewSet(current_user, db)
    return await viewset.add_evaluation(task_id, eval_in)


@router.get("/{task_id}/evaluations", response_model=List[EvaluationRead])
async def list_evaluations(
    task_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = EvaluationViewSet(current_user, db)
    return await viewset.list_evaluations(task_id)

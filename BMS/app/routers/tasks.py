from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.utils.services import get_task_or_404
from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.models.comment import Comment
from app.models.evaluation import Evaluation
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
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
    """
    Список задач, созданных или назначенных пользователю.
    """
    if not current_user.team_id:
        return []

    stmt = (
        select(Task)
        .where(
            (Task.assignee_id == current_user.id) |
            (Task.creator_id == current_user.id)
        )
        .options(
            selectinload(Task.comments),
            selectinload(Task.evaluations)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Создание задачи (только для менеджера/админа в команде).
    """
    task = Task(
        title=task_in.title,
        description=task_in.description,
        deadline=task_in.deadline,
        creator_id=current_user.id,
        assignee_id=task_in.assignee_id,
        status=task_in.status,
    )
    db.add(task)
    await db.commit()

    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.comments),
            selectinload(Task.evaluations),
        )
        .where(Task.id == task.id)
    )
    task = result.scalar_one()
    return task


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Обновление задачи (создатель, менеджер или админ команды).
    """
    task = await get_task_or_404(task_id, db)

    same_team = task.creator.team_id == current_user.team_id
    is_author = task.creator_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    is_manager = current_user.role == UserRole.MANAGER

    if not (is_admin or (is_manager and same_team) or is_author):
        raise HTTPException(403, detail="Нет прав на изменение задачи")

    data = task_in.model_dump(exclude_none=True)
    await db.execute(update(Task).where(Task.id == task_id).values(**data))
    await db.commit()

    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.comments),
            selectinload(Task.evaluations),
        )
        .where(Task.id == task_id)
    )
    task = result.scalar_one()
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Удаление задачи (только автор или админ).
    """
    task = await get_task_or_404(task_id, db)

    if current_user.role != UserRole.ADMIN and task.creator_id != current_user.id:
        raise HTTPException(403, detail="Нет прав на удаление задачи")

    await db.execute(delete(Task).where(Task.id == task_id))
    await db.commit()


# -------------------------------------------------------------------
# Эндпоинты по комментариям
# -------------------------------------------------------------------

@router.post("/{task_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def add_comment(
    task_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Добавление комментария (если пользователь в команде создателя/исполнителя).
    """
    task = await get_task_or_404(task_id, db)

    if current_user.role != UserRole.ADMIN and current_user.team_id not in {
        task.creator.team_id, task.assignee.team_id
    }:
        raise HTTPException(403, detail="Нет доступа к комментированию задачи")

    comment = Comment(text=comment_in.text, author_id=current_user.id, task_id=task_id)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@router.get("/{task_id}/comments", response_model=List[CommentRead])
async def list_comments(
    task_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Получить список комментариев по задаче.
    """
    # вместо task.comments делаем явный запрос
    stmt = select(Comment).where(Comment.task_id == task_id)
    result = await db.execute(stmt)
    return result.scalars().all()


# -------------------------------------------------------------------
# Эндпоинты по оценкам
# -------------------------------------------------------------------

@router.post("/{task_id}/evaluations", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
async def add_evaluation(
    task_id: int,
    eval_in: EvaluationCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Добавить оценку задаче (только DONE, и только менеджером/админом).
    """
    task = await get_task_or_404(task_id, db)

    if task.status != TaskStatus.DONE:
        raise HTTPException(400, detail="Задача ещё не завершена")

    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(403, detail="Нет прав на выставление оценки")

    exists = await db.execute(
        select(Evaluation).where(Evaluation.task_id == task_id)
    )
    if exists.scalars().first():
        raise HTTPException(400, detail="Оценка уже существует")

    evaluation = Evaluation(
        score=eval_in.score,
        evaluator_id=current_user.id,
        task_id=task_id,
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


@router.get("/{task_id}/evaluations", response_model=List[EvaluationRead])
async def list_evaluations(
    task_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Получить оценки по задаче.
    """
    # вместо task.evaluations делаем явный запрос
    stmt = select(Evaluation).where(Evaluation.task_id == task_id)
    result = await db.execute(stmt)
    return result.scalars().all()

from datetime import date, datetime
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.evaluation import Evaluation
from app.models.team import Team
from app.models.user import User
from app.schemas.user import UserUpdate, UserRead
from app.core.database import get_async_session
from app.core.auth import current_user


router = APIRouter(prefix="/me", tags=["Пользователи"])

# -------------------------------------------------------------------
# Эндпоинты
# -------------------------------------------------------------------

@router.get("/", response_model=UserRead)
async def get_my_profile(
    user: User = Depends(current_user)
):
    """Получить информацию о себе."""
    return user


@router.patch("/", response_model=UserRead)
async def update_profile(
    user_update: UserUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Обновить информацию о себе."""
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить свой профиль."""
    await session.delete(user)
    await session.commit()


@router.post("/join_by_code")
async def join_team_by_code(
    data: str = Body(..., min_length=8, max_length=8, description="Код команды (ровно 8 символов)"),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Присоединиться к команде по коду."""
    if user.team_id:
        raise HTTPException(status_code=400, detail="Вы уже в команде.")

    result = await session.execute(
        select(Team).where(Team.invite_code == data)
    )
    team = result.scalars().first()

    if not team:
        raise HTTPException(status_code=404, detail="Команда с таким кодом не найдена.")

    user.team = team
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return {"message": f"Вы успешно присоединились к команде '{team.name}'."}


@router.get("/average_evaluation")
async def get_average_evaluation(
    date_from: date = Query(..., alias="from", description="Начало периода"),
    date_to: date = Query(..., alias="to", description="Конец периода"),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Получить среднюю оценку за указанный период."""
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="Некорректный период: 'from' позже 'to'")

    date_to_datetime = datetime.combine(date_to, datetime.max.time())

    stmt = (
        select(func.avg(Evaluation.score))
        .join(Task, Evaluation.task_id == Task.id)
        .where(
            Task.assignee_id == user.id,
            Evaluation.created_at >= datetime.combine(date_from, datetime.min.time()),
            Evaluation.created_at <= date_to_datetime,
        )
    )
    result = await session.execute(stmt)
    average = result.scalar()

    return {"average_score": round(average, 2) if average is not None else None}

from datetime import date, datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole
from app.models.task import Task
from app.models.team import Team
from app.models.meeting import Meeting, meeting_participants_association


async def get_tasks_for_date(
    db: AsyncSession, team_id: int, target: date
) -> List[Task]:
    """
    Получить задачи с дедлайном на конкретную дату,
    фильтруя по команде (через assignee или creator).
    """
    stmt = (
        select(Task)
        .where(Task.deadline.isnot(None))
        .where(func.date(Task.deadline) == target)
        .where(
            or_(
                Task.assignee.has(team_id=team_id),
                Task.creator.has(team_id=team_id)
            )
        )
        .options(
            selectinload(Task.comments),
            selectinload(Task.evaluations),
            selectinload(Task.creator),
            selectinload(Task.assignee),
        )
    )
    res = await db.execute(stmt)
    return res.scalars().all()


async def get_meetings_for_date(
    db: AsyncSession, user_id: int, target: date
) -> List[Meeting]:
    """
    Получить встречи пользователя на конкретную дату.
    """
    stmt = (
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .where(func.date(Meeting.start_time) == target)
        .join(Meeting.participants)
        .where(Meeting.participants.any(id=user_id))
    )
    res = await db.execute(stmt)
    return res.scalars().all()


async def get_meeting_or_404(meeting_id: int, db: AsyncSession) -> Meeting:
    """
    Получить встречу по ID или выбросить 404 ошибку.
    """
    res = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .where(Meeting.id == meeting_id)
    )
    meeting = res.scalars().first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Встреча не найдена")
    return meeting


async def check_time_conflicts(
    user_ids: List[int],
    start: datetime,
    end: datetime,
    db: AsyncSession,
    exclude_meeting_id: Optional[int] = None,
) -> None:
    """
    Проверяет пересечения по времени для списка пользователей.
    Если хотя бы у одного есть пересечение — выбрасывает ошибку.
    """
    stmt = (
        select(meeting_participants_association.c.user_id)
        .join(Meeting, meeting_participants_association.c.meeting_id == Meeting.id)
        .where(meeting_participants_association.c.user_id.in_(user_ids))
        .where(and_(
            Meeting.start_time < end,
            Meeting.end_time > start
        ))
    )

    if exclude_meeting_id:
        stmt = stmt.where(Meeting.id != exclude_meeting_id)

    result = await db.execute(stmt)
    busy_user_ids = result.scalars().all()

    if busy_user_ids:
        ids_str = ', '.join(map(str, set(busy_user_ids)))
        raise HTTPException(
            status_code=400,
            detail=f"Пользователи с ID {ids_str} уже заняты в это время"
        )


async def get_team_or_404(team_id: int, db: AsyncSession) -> Team:
    """
    Получить команду по ID или выбросить 404 ошибку.
    """
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.members))
        .where(Team.id == team_id)
    )
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")
    return team


async def get_task_or_404(task_id: int, db: AsyncSession) -> Task:
    """
    Получить задачу с комментариями и оценками по ID или выбросить 404 ошибку.
    """
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.comments),
            selectinload(Task.evaluations),
            selectinload(Task.creator),
            selectinload(Task.assignee),
        )
        .where(Task.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


def assert_team_admin_or_global_admin(current_user: User, team: Team) -> None:
    """
    Проверить, что текущий пользователь - глобальный админ
    или админ команды. В противном случае выбросить 403 ошибку.
    """
    if current_user.role != UserRole.ADMIN or team.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения операции")


async def get_user_or_404(user_id: int, db: AsyncSession) -> User:
    """
    Получить пользователя по ID или выбросить 404 ошибку.
    """
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

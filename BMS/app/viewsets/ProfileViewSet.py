from datetime import date, datetime
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.evaluation import Evaluation
from app.models.team import Team
from app.models.user import User
from app.schemas.user import UserUpdate


class ProfileViewSet:
    def __init__(self, user: User, session: AsyncSession):
        self.user = user
        self.session = session

    async def get_my_profile(self) -> User:
        return self.user

    async def update_profile(self, user_update: UserUpdate) -> User:
        for field, value in user_update.dict(exclude_unset=True).items():
            setattr(self.user, field, value)

        self.session.add(self.user)
        await self.session.commit()
        await self.session.refresh(self.user)
        return self.user

    async def delete_profile(self) -> None:
        await self.session.delete(self.user)
        await self.session.commit()

    async def join_team_by_code(self, code: str) -> dict:
        if self.user.team_id:
            raise HTTPException(status_code=400, detail="Вы уже в команде.")

        result = await self.session.execute(
            select(Team).where(Team.invite_code == code)
        )
        team = result.scalars().first()

        if not team:
            raise HTTPException(status_code=404, detail="Команда с таким кодом не найдена.")

        self.user.team = team
        self.session.add(self.user)
        await self.session.commit()
        await self.session.refresh(self.user)

        return {"message": f"Вы успешно присоединились к команде '{team.name}'."}

    async def get_average_evaluation(self, date_from: date, date_to: date) -> dict:
        if date_from > date_to:
            raise HTTPException(status_code=400, detail="Некорректный период: 'from' позже 'to'")

        date_to_datetime = datetime.combine(date_to, datetime.max.time())

        stmt = (
            select(func.avg(Evaluation.score))
            .join(Task, Evaluation.task_id == Task.id)
            .where(
                Task.assignee_id == self.user.id,
                Evaluation.created_at >= datetime.combine(date_from, datetime.min.time()),
                Evaluation.created_at <= date_to_datetime,
            )
        )
        result = await self.session.execute(stmt)
        average = result.scalar()

        return {"average_score": round(average, 2) if average is not None else None}

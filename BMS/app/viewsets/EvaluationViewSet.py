from typing import List
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.services import get_task_or_404
from app.models.evaluation import Evaluation
from app.models.task import TaskStatus
from app.models.user import User, UserRole
from app.schemas.evaluation import EvaluationCreate


class EvaluationViewSet:
    def __init__(self, current_user: User, db: AsyncSession):
        self.current_user = current_user
        self.db = db

    async def add_evaluation(self, task_id: int, eval_in: EvaluationCreate) -> Evaluation:
        task = await get_task_or_404(task_id, self.db)

        if task.status != TaskStatus.DONE:
            raise HTTPException(400, detail="Задача ещё не завершена")

        if self.current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
            raise HTTPException(403, detail="Нет прав на выставление оценки")

        exists = await self.db.execute(
            select(Evaluation).where(Evaluation.task_id == task_id)
        )
        if exists.scalars().first():
            raise HTTPException(400, detail="Оценка уже существует")

        evaluation = Evaluation(
            score=eval_in.score,
            evaluator_id=self.current_user.id,
            task_id=task_id,
        )
        self.db.add(evaluation)
        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation

    async def list_evaluations(self, task_id: int) -> List[Evaluation]:
        stmt = select(Evaluation).where(Evaluation.task_id == task_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

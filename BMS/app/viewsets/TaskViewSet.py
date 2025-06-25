from typing import List
from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.utils.services import get_task_or_404
from app.models.task import Task
from app.models.user import User, UserRole
from app.schemas.task import TaskCreate, TaskUpdate


class TaskViewSet:
    def __init__(self, current_user: User, db: AsyncSession):
        self.current_user = current_user
        self.db = db

    async def list_tasks(self) -> List[Task]:
        if not self.current_user.team_id:
            return []

        stmt = (
            select(Task)
            .where(
                (Task.assignee_id == self.current_user.id) |
                (Task.creator_id == self.current_user.id)
            )
            .options(
                selectinload(Task.comments),
                selectinload(Task.evaluations)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_task(self, task_in: TaskCreate) -> Task:
        task = Task(
            title=task_in.title,
            description=task_in.description,
            deadline=task_in.deadline,
            creator_id=self.current_user.id,
            assignee_id=task_in.assignee_id,
            status=task_in.status,
        )
        self.db.add(task)
        await self.db.commit()

        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.comments),
                selectinload(Task.evaluations),
            )
            .where(Task.id == task.id)
        )
        task = result.scalar_one()
        return task

    async def update_task(self, task_id: int, task_in: TaskUpdate) -> Task:
        task = await get_task_or_404(task_id, self.db)

        same_team = task.creator.team_id == self.current_user.team_id
        is_author = task.creator_id == self.current_user.id
        is_admin = self.current_user.role == UserRole.ADMIN
        is_manager = self.current_user.role == UserRole.MANAGER

        if not (is_admin or (is_manager and same_team) or is_author):
            raise HTTPException(403, detail="Нет прав на изменение задачи")

        data = task_in.model_dump(exclude_none=True)
        await self.db.execute(update(Task).where(Task.id == task_id).values(**data))
        await self.db.commit()

        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.comments),
                selectinload(Task.evaluations),
            )
            .where(Task.id == task_id)
        )
        task = result.scalar_one()
        return task

    async def delete_task(self, task_id: int) -> None:
        task = await get_task_or_404(task_id, self.db)

        if self.current_user.role != UserRole.ADMIN and task.creator_id != self.current_user.id:
            raise HTTPException(403, detail="Нет прав на удаление задачи")

        await self.db.execute(delete(Task).where(Task.id == task_id))
        await self.db.commit()

from typing import List
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.services import get_task_or_404
from app.models.comment import Comment
from app.models.user import User, UserRole
from app.schemas.comment import CommentCreate


class CommentViewSet:
    def __init__(self, current_user: User, db: AsyncSession):
        self.current_user = current_user
        self.db = db

    async def add_comment(self, task_id: int, comment_in: CommentCreate) -> Comment:
        task = await get_task_or_404(task_id, self.db)

        if self.current_user.role != UserRole.ADMIN and self.current_user.team_id not in {
            task.creator.team_id, task.assignee.team_id
        }:
            raise HTTPException(403, detail="Нет доступа к комментированию задачи")

        comment = Comment(text=comment_in.text, author_id=self.current_user.id, task_id=task_id)
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def list_comments(self, task_id: int) -> List[Comment]:
        stmt = select(Comment).where(Comment.task_id == task_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
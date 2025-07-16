from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole
from app.schemas.meeting import MeetingRead, MeetingCreate, MeetingUpdate
from app.utils.services import get_meeting_or_404, check_time_conflicts
from app.models.meeting import Meeting, meeting_participants_association


class MeetingViewSet:
    def __init__(self, current_user: User, db: AsyncSession):
        self.current_user = current_user
        self.db = db

    async def list_meetings(self) -> List[MeetingRead]:
        meetings_result = await self.db.execute(
            select(Meeting)
            .options(selectinload(Meeting.participants))
            .join(meeting_participants_association)
            .where(meeting_participants_association.c.user_id == self.current_user.id)
        )
        meetings = meetings_result.scalars().all()

        return [
            MeetingRead(
                id=m.id,
                title=m.title,
                start_time=m.start_time,
                end_time=m.end_time,
                creator_id=m.creator_id,
                participants=[user.id for user in m.participants],
            )
            for m in meetings
        ]

    async def create_meeting(self, meeting_in: MeetingCreate) -> MeetingRead:
        if self.current_user.role != UserRole.MANAGER:
            raise HTTPException(status_code=403, detail="Только менеджер может создавать встречи")

        participants = set(meeting_in.participants)
        participants.add(self.current_user.id)

        await check_time_conflicts(
            user_ids=list(participants),
            start=meeting_in.start_time,
            end=meeting_in.end_time,
            db=self.db
        )

        result = await self.db.execute(select(User).where(User.id.in_(participants)))
        users = result.scalars().all()
        if len(users) != len(participants):
            raise HTTPException(status_code=404, detail="Один или несколько участников не найдены")

        meeting = Meeting(
            title=meeting_in.title,
            start_time=meeting_in.start_time,
            end_time=meeting_in.end_time,
            creator_id=self.current_user.id,
            participants=users,
        )

        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting, attribute_names=["participants"])

        return MeetingRead(
            id=meeting.id,
            title=meeting.title,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            creator_id=meeting.creator_id,
            participants=[user.id for user in meeting.participants],
        )

    async def update_meeting(self, meeting_id: int, meeting_in: MeetingUpdate) -> MeetingRead:
        if self.current_user.role != UserRole.MANAGER:
            raise HTTPException(status_code=403, detail="Только менеджер может обновлять встречи")

        meeting = await get_meeting_or_404(meeting_id, self.db)

        if meeting.creator_id != self.current_user.id:
            raise HTTPException(status_code=403, detail="Можно редактировать только свои встречи")

        data = meeting_in.model_dump(exclude_none=True)

        new_start = data.get("start_time", meeting.start_time)
        new_end = data.get("end_time", meeting.end_time)
        new_participant_ids = set(data.get("participants", [u.id for u in meeting.participants]))
        new_participant_ids.add(meeting.creator_id)

        await check_time_conflicts(
            user_ids=list(new_participant_ids),
            start=new_start,
            end=new_end,
            db=self.db,
            exclude_meeting_id=meeting_id
        )

        await self.db.execute(
            update(Meeting)
            .where(Meeting.id == meeting_id)
            .values(
                title=data.get("title", meeting.title),
                start_time=new_start,
                end_time=new_end
            )
        )

        await self.db.execute(
            delete(meeting_participants_association)
            .where(meeting_participants_association.c.meeting_id == meeting_id)
        )

        for uid in new_participant_ids:
            await self.db.execute(
                meeting_participants_association.insert().values(
                    meeting_id=meeting_id,
                    user_id=uid
                )
            )

        await self.db.commit()
        updated = await get_meeting_or_404(meeting_id, self.db)
        return MeetingRead(
            id=updated.id,
            title=updated.title,
            start_time=updated.start_time,
            end_time=updated.end_time,
            creator_id=updated.creator_id,
            participants=[user.id for user in updated.participants],
        )

    async def delete_meeting(self, meeting_id: int) -> None:
        if self.current_user.role != UserRole.MANAGER:
            raise HTTPException(status_code=403, detail="Только менеджер может удалять встречи")

        meeting = await get_meeting_or_404(meeting_id, self.db)

        if meeting.creator_id != self.current_user.id:
            raise HTTPException(status_code=403, detail="Можно удалять только свои встречи")

        await self.db.execute(
            delete(meeting_participants_association)
            .where(meeting_participants_association.c.meeting_id == meeting_id)
        )

        await self.db.execute(
            delete(Meeting).where(Meeting.id == meeting_id)
        )

        await self.db.commit()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.auth import current_active_user
from app.models.user import User, UserRole
from app.schemas.meeting import MeetingRead, MeetingCreate, MeetingUpdate
from app.utils.services import get_meeting_or_404, check_time_conflicts
from app.models.meeting import Meeting, meeting_participants_association

router = APIRouter(prefix="/meetings", tags=["Встречи"])

# -------------------------------------------------------------------
# Эндпоинты
# -------------------------------------------------------------------

@router.get(
    "/",
    response_model=List[MeetingRead],
    description="Список встреч текущего пользователя."
)
async def list_meetings(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    meetings = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .join(meeting_participants_association)
        .where(meeting_participants_association.c.user_id == current_user.id)
    )
    meetings = meetings.scalars().all()

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


@router.post(
    "/",
    response_model=MeetingRead,
    status_code=status.HTTP_201_CREATED,
    description="Создание новой встречи. Только для менеджеров. Проверка на пересечения по времени у участников."
)
async def create_meeting(
    meeting_in: MeetingCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Только менеджер может создавать встречи")

    participants = set(meeting_in.participants)
    participants.add(current_user.id)

    await check_time_conflicts(
        user_ids=list(participants),
        start=meeting_in.start_time,
        end=meeting_in.end_time,
        db=db
    )

    result = await db.execute(select(User).where(User.id.in_(participants)))
    users = result.scalars().all()
    if len(users) != len(participants):
        raise HTTPException(status_code=404, detail="Один или несколько участников не найдены")

    # Подставляем объекты пользователей
    meeting = Meeting(
        title=meeting_in.title,
        start_time=meeting_in.start_time,
        end_time=meeting_in.end_time,
        creator_id=current_user.id,
        participants=users,
    )

    db.add(meeting)
    await db.commit()
    await db.refresh(meeting, attribute_names=["participants"])

    return MeetingRead(
        id=meeting.id,
        title=meeting.title,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        creator_id=meeting.creator_id,
        participants=[user.id for user in meeting.participants],
    )


@router.put(
    "/{meeting_id}",
    response_model=MeetingRead,
    description="Обновление встречи. Только для менеджеров, если они являются создателями встречи."
)
async def update_meeting(
    meeting_id: int,
    meeting_in: MeetingUpdate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Только менеджер может обновлять встречи")

    meeting = await get_meeting_or_404(meeting_id, db)

    if meeting.creator_id != current_user.id:
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
        db=db,
        exclude_meeting_id=meeting_id
    )

    await db.execute(
        update(Meeting)
        .where(Meeting.id == meeting_id)
        .values(
            title=data.get("title", meeting.title),
            start_time=new_start,
            end_time=new_end
        )
    )

    await db.execute(
        delete(meeting_participants_association)
        .where(meeting_participants_association.c.meeting_id == meeting_id)
    )

    for uid in new_participant_ids:
        await db.execute(
            meeting_participants_association.insert().values(
                meeting_id=meeting_id,
                user_id=uid
            )
        )

    await db.commit()
    updated = await get_meeting_or_404(meeting_id, db)
    return MeetingRead(
        id=updated.id,
        title=updated.title,
        start_time=updated.start_time,
        end_time=updated.end_time,
        creator_id=updated.creator_id,
        participants=[user.id for user in updated.participants],
    )


@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Удаление встречи. Только для менеджеров, если они являются создателями встречи."
)
async def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Только менеджер может удалять встречи")

    meeting = await get_meeting_or_404(meeting_id, db)

    if meeting.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно удалять только свои встречи")

    await db.execute(
        delete(meeting_participants_association)
        .where(meeting_participants_association.c.meeting_id == meeting_id)
    )

    await db.execute(
        delete(Meeting).where(Meeting.id == meeting_id)
    )

    await db.commit()


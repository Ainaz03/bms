from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.viewsets.MeetingViewSet import MeetingViewSet
from app.core.database import get_async_session
from app.core.auth import current_active_user
from app.models.user import User
from app.schemas.meeting import MeetingRead, MeetingCreate, MeetingUpdate

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
    viewset = MeetingViewSet(current_user, db)
    return await viewset.list_meetings()


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
    viewset = MeetingViewSet(current_user, db)
    return await viewset.create_meeting(meeting_in)


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
    viewset = MeetingViewSet(current_user, db)
    return await viewset.update_meeting(meeting_id, meeting_in)


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
    viewset = MeetingViewSet(current_user, db)
    await viewset.delete_meeting(meeting_id)
    
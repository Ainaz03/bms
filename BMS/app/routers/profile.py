from datetime import date
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.viewsets.ProfileViewSet import ProfileViewSet
from app.models.user import User
from app.schemas.user import UserUpdate, UserRead
from app.core.database import get_async_session
from app.core.auth import current_user


router = APIRouter(prefix="/me", tags=["Пользователи"])

# -------------------------------------------------------------------
# Эндпоинты
# -------------------------------------------------------------------

@router.get("/", response_model=UserRead)
async def get_my_profile(user: User = Depends(current_user)):
    viewset = ProfileViewSet(user, None)
    return await viewset.get_my_profile()


@router.patch("/", response_model=UserRead)
async def update_profile(
    user_update: UserUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    viewset = ProfileViewSet(user, session)
    return await viewset.update_profile(user_update)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    viewset = ProfileViewSet(user, session)
    await viewset.delete_profile()


@router.post("/join_by_code")
async def join_team_by_code(
    data: str = Body(..., min_length=8, max_length=8, description="Код команды (ровно 8 символов)"),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    viewset = ProfileViewSet(user, session)
    return await viewset.join_team_by_code(data)


@router.get("/average_evaluation")
async def get_average_evaluation(
    date_from: date = Query(..., alias="from", description="Начало периода"),
    date_to: date = Query(..., alias="to", description="Конец периода"),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    viewset = ProfileViewSet(user, session)
    return await viewset.get_average_evaluation(date_from, date_to)
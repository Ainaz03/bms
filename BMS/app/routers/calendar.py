from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.viewsets.CalendarViewSet import CalendarViewSet
from app.core.database import get_async_session
from app.core.auth import current_active_user
from app.models.user import User


router = APIRouter(prefix="/calendar", tags=["Календарь"])

# -------------------------------------------------------------------
# Эндпоинты
# -------------------------------------------------------------------

@router.get(
    "/daily/{target_date}",
    response_class=PlainTextResponse,
    description="Дневной вид: текстовая таблица задач и встреч на указанную дату YYYY-MM-DD"
)
async def daily_calendar(
    target_date: str,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = CalendarViewSet(current_user, db)
    return await viewset.daily_calendar(target_date)


@router.get(
    "/monthly/{year}/{month}",
    response_class=PlainTextResponse,
    description="Месячный вид: текстовая таблица с количеством задач и встреч на каждый день"
)
async def monthly_calendar(
    year: int,
    month: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = CalendarViewSet(current_user, db)
    return await viewset.monthly_calendar(year, month)

from datetime import datetime, date
import calendar as pycal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.services import get_meetings_for_date, get_tasks_for_date
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
    try:
        d = datetime.fromisoformat(target_date).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты, ожидается YYYY-MM-DD")

    if not current_user.team_id:
        return "Вы не состоите в команде."

    tasks = await get_tasks_for_date(db, current_user.team_id, d)
    meetings = await get_meetings_for_date(db, current_user.id, d)

    lines = ["Время      | Тип     | Заголовок", "-" * 40]

    for t in sorted(tasks, key=lambda x: x.deadline or datetime.min):
        tm = t.deadline.time().strftime("%H:%M") if t.deadline else "--:--"
        lines.append(f"{tm:<10}| Задача  | {t.title}")

    for m in sorted(meetings, key=lambda x: x.start_time):
        tm = m.start_time.time().strftime("%H:%M")
        lines.append(f"{tm:<10}| Встреча| {m.title}")

    if len(lines) == 2:
        lines.append("Событий нет.")

    return "\n".join(lines)


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
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="Месяц должен быть от 1 до 12")

    if not current_user.team_id:
        return "Вы не состоите в команде."

    _, days_in_month = pycal.monthrange(year, month)
    header = "Дата       | Задач | Встреч"
    lines = [header, "-" * len(header)]

    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        tasks = await get_tasks_for_date(db, current_user.team_id, d)
        meetings = await get_meetings_for_date(db, current_user.id, d)
        lines.append(f"{d.isoformat():<10}| {len(tasks):^5} | {len(meetings):^6}")

    return "\n".join(lines)

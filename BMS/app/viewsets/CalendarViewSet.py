import calendar as pycal
from datetime import datetime, date
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.services import get_meetings_for_date, get_tasks_for_date
from app.models.user import User


class CalendarViewSet:
    def __init__(self, current_user: User, db: AsyncSession):
        self.current_user = current_user
        self.db = db

    async def daily_calendar(self, target_date_str: str) -> str:
        try:
            d = datetime.fromisoformat(target_date_str).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат даты, ожидается YYYY-MM-DD")

        if not self.current_user.team_id:
            return "Вы не состоите в команде."

        tasks = await get_tasks_for_date(self.db, self.current_user.team_id, d)
        meetings = await get_meetings_for_date(self.db, self.current_user.id, d)

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

    async def monthly_calendar(self, year: int, month: int) -> str:
        if not 1 <= month <= 12:
            raise HTTPException(status_code=400, detail="Месяц должен быть от 1 до 12")

        if not self.current_user.team_id:
            return "Вы не состоите в команде."

        _, days_in_month = pycal.monthrange(year, month)
        header = "Дата       | Задач | Встреч"
        lines = [header, "-" * len(header)]

        for day in range(1, days_in_month + 1):
            d = date(year, month, day)
            tasks = await get_tasks_for_date(self.db, self.current_user.team_id, d)
            meetings = await get_meetings_for_date(self.db, self.current_user.id, d)
            lines.append(f"{d.isoformat():<10}| {len(tasks):^5} | {len(meetings):^6}")

        return "\n".join(lines)

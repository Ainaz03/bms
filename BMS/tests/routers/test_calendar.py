import pytest
from datetime import datetime, date
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.core.auth import current_active_user
import app.routers.calendar as cal_router

class Dummy:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

@pytest.mark.asyncio
async def test_daily_invalid_date(async_client: AsyncClient, db_session):
    user = Dummy(id=1, team_id=1)
    app.dependency_overrides[current_active_user] = lambda: user

    resp = await async_client.get("/calendar/daily/not-a-date")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["detail"] == "Неверный формат даты, ожидается YYYY-MM-DD"

    app.dependency_overrides.pop(current_active_user)

@pytest.mark.asyncio
async def test_daily_no_team(async_client: AsyncClient, db_session):
    user = Dummy(id=1, team_id=None)
    app.dependency_overrides[current_active_user] = lambda: user

    today = date.today().isoformat()
    resp = await async_client.get(f"/calendar/daily/{today}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.text == "Вы не состоите в команде."

    app.dependency_overrides.pop(current_active_user)


@pytest.mark.asyncio
async def test_monthly_invalid_month(async_client: AsyncClient, db_session):
    user = Dummy(id=1, team_id=1)
    app.dependency_overrides[current_active_user] = lambda: user

    resp = await async_client.get("/calendar/monthly/2025/13")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["detail"] == "Месяц должен быть от 1 до 12"

    app.dependency_overrides.pop(current_active_user)

@pytest.mark.asyncio
async def test_monthly_no_team(async_client: AsyncClient, db_session):
    user = Dummy(id=1, team_id=None)
    app.dependency_overrides[current_active_user] = lambda: user

    resp = await async_client.get("/calendar/monthly/2025/6")
    assert resp.status_code == 200
    assert resp.text == "Вы не состоите в команде."

    app.dependency_overrides.pop(current_active_user)


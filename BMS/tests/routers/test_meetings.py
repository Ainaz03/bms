# tests/routers/test_meetings.py
import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.main import app
from app.core.auth import current_active_user
from app.utils.services import check_time_conflicts
from app.models.user import User, UserRole
from app.models.meeting import Meeting, meeting_participants_association
from app.schemas.meeting import MeetingCreate, MeetingUpdate


@pytest.mark.asyncio
async def test_list_meetings(async_client: AsyncClient, db_session):
    # подготовка: два пользователя и две встречи
    manager = User(email="m@e.com", hashed_password="x", role=UserRole.MANAGER,
                    is_active=True, is_superuser=False, is_verified=True)
    member = User(email="u@e.com", hashed_password="x", role=UserRole.USER,
                   is_active=True, is_superuser=False, is_verified=True)
    db_session.add_all([manager, member])
    await db_session.commit()
    await db_session.refresh(manager)
    await db_session.refresh(member)

    # создаём вручную две встречи: одна с обоими участниками, другая — только с менеджером
    now = datetime.utcnow()
    meeting1 = Meeting(
        title="Team Sync",
        start_time=now,
        end_time=now + timedelta(hours=1),
        creator_id=manager.id,
        participants=[manager, member]
    )
    meeting2 = Meeting(
        title="Private",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=1),
        creator_id=manager.id,
        participants=[manager]
    )
    db_session.add_all([meeting1, meeting2])
    await db_session.commit()
    await db_session.refresh(meeting1)
    await db_session.refresh(meeting2)

    # override current user = обычный участник
    app.dependency_overrides[current_active_user] = lambda: member

    # GET /meetings/
    resp = await async_client.get("/meetings/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    # участник должен увидеть только встречу1
    ids = [m["id"] for m in data]
    assert meeting1.id in ids
    assert meeting2.id not in ids

    app.dependency_overrides.pop(current_active_user)


@pytest.mark.asyncio
async def test_create_meeting_forbidden(async_client: AsyncClient, db_session):
    user = User(email="x@e.com", hashed_password="x", role=UserRole.USER,
                is_active=True, is_superuser=False, is_verified=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides[current_active_user] = lambda: user

    payload = {
        "title": "New",
        "start_time": datetime.utcnow().isoformat(),
        "end_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "participants": []
    }
    resp = await async_client.post("/meetings/", json=payload)
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    app.dependency_overrides.pop(current_active_user)


import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.core.auth import current_active_user
from app.models.user import User, UserRole
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamMemberAdd, TeamMemberRoleUpdate


@pytest.mark.asyncio
async def test_create_team_success(async_client: AsyncClient, db_session):
    # 1) Подготовка: создаём в БД администратора системы
    admin = User(
        email="admin@example.com",
        hashed_password="irrelevant",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    # 2) Подмена current_active_user → наш admin
    app.dependency_overrides[current_active_user] = lambda: admin

    # 3) Вызов эндпоинта
    payload = {"name": "Team Alpha"}
    response = await async_client.post("/teams/", json=payload)

    # 4) Ассерты
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Team Alpha"
    assert data["admin_id"] == admin.id
    assert data["members"] == []

    # 5) Сброс override
    app.dependency_overrides.pop(current_active_user)


@pytest.mark.asyncio
async def test_create_team_forbidden(async_client: AsyncClient, db_session):
    # Пользователь без роли ADMIN
    user = User(
        email="user@example.com",
        hashed_password="irrelevant",
        role=UserRole.USER,
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides[current_active_user] = lambda: user

    response = await async_client.post("/teams/", json={"name": "X"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

    app.dependency_overrides.pop(current_active_user)


@pytest.mark.asyncio
async def test_read_team_and_members(async_client: AsyncClient, db_session):
    # 1) Создаём админа в чистой БД
    admin = User(
        email="a@e.com", hashed_password="x",
        role=UserRole.ADMIN, is_active=True,
        is_superuser=False, is_verified=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    # 2) Override user
    app.dependency_overrides[current_active_user] = lambda: admin

    # 3) Создаём команду через API
    resp_create = await async_client.post("/teams/", json={"name": "Bravo"})
    assert resp_create.status_code == status.HTTP_201_CREATED
    team = resp_create.json()

    # 4) GET и проверка — на чистой БД members будет []
    resp_get = await async_client.get(f"/teams/{team['id']}")
    assert resp_get.status_code == status.HTTP_200_OK
    assert resp_get.json()["members"] == []

    app.dependency_overrides.pop(current_active_user)


import pytest
from httpx import AsyncClient, ASGITransport
from datetime import date, datetime, timedelta

from app.main import app


@pytest.fixture
async def registered_user():
    """Создаёт пользователя через API и возвращает access_token и email."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = "testuser@example.com"
        password = "strongpassword123"

        # Регистрация
        await ac.post("/auth/register", json={"email": email, "password": password})

        # Авторизация
        login_response = await ac.post("/auth/login", data={
            "username": email,
            "password": password
        })
        token = login_response.json()["access_token"]

        return {"email": email, "password": password, "token": token}


@pytest.mark.asyncio
async def test_get_my_profile(registered_user):
    user = await registered_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers = {"Authorization": f"Bearer {user['token']}"}

        resp = await ac.get("/me/")
        assert resp.status_code == 200
        assert resp.json()["email"] == user["email"]


@pytest.mark.asyncio
async def test_update_profile(registered_user):
    user = await registered_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers = {"Authorization": f"Bearer {user['token']}"}

        new_email = "updated@example.com"
        resp = await ac.patch("/me/", json={"email": new_email})
        assert resp.status_code == 200
        assert resp.json()["email"] == new_email


@pytest.mark.asyncio
async def test_get_average_evaluation(registered_user):
    # Пока предполагается, что вручную в БД уже есть Evaluation (task -> score = 4.5)
    user = await registered_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers = {"Authorization": f"Bearer {user['token']}"}

        today = date.today().isoformat()
        resp = await ac.get(f"/me/average_evaluation?from={today}&to={today}")
        # Если нет оценок — получим 404, иначе 200
        assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_average_evaluation_invalid_period(registered_user):
    user = await registered_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers = {"Authorization": f"Bearer {user['token']}"}

        from_date = (date.today() + timedelta(days=1)).isoformat()
        to_date = date.today().isoformat()
        resp = await ac.get(f"/me/average_evaluation?from={from_date}&to={to_date}")
        assert resp.status_code == 400
        assert "Некорректный период" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_delete_profile(registered_user):
    user = await registered_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers = {"Authorization": f"Bearer {user['token']}"}

        resp = await ac.delete("/me/")
        assert resp.status_code == 204

        # Попробуем получить профиль после удаления — ожидаем 401
        resp2 = await ac.get("/me/")
        assert resp2.status_code == 401

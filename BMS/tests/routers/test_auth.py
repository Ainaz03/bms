import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.main import app        


@pytest.mark.asyncio
async def test_register_login_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Сначала регистрация
        await ac.post("/auth/register", json={
            "email": "loginuser@example.com",
            "password": "strongpassword123"
        })
        response = await ac.post("/auth/register", json={
            "email": "testuser@example.com",
            "password": "strongpassword123"
        })
        assert response.status_code in (200, 201)

        # Теперь логин
        response = await ac.post("/auth/login", data={
            "username": "loginuser@example.com",
            "password": "strongpassword123"
        })
        assert response.status_code == 200

# tests/conftest.py
import os
from dotenv import load_dotenv

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import get_async_session, Base  # import Base from your models
from app.main import app

# 2) In-memory SQLite URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 3) Создаём движок и sessionmaker
engine_test = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
TestSessionLocal = sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db():
    """
    Перед всеми тестами: создать в памяти все таблицы по вашим моделям.
    После — просто выкинуть движок (сессия в памяти удалится сама).
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine_test.dispose()


@pytest_asyncio.fixture
async def db_session(init_test_db) -> AsyncSession:
    """Каждый тест получает свою сессию на тот же движок."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
def override_db_dependency(db_session: AsyncSession):
    """
    Автоматически подменяем get_async_session → нашу in‑memory сессию.
    """
    async def _get_test_session():
        yield db_session

    app.dependency_overrides[get_async_session] = _get_test_session


@pytest_asyncio.fixture
async def async_client() -> "AsyncClient":
    """
    Асинхронный HTTP клиент, привязанный к FastAPI-приложению.
    """
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

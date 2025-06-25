from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


# -------------------------------------------------------------------
# Инициализация SQLAlchemy
# -------------------------------------------------------------------

# --- Движок PostgreSQL ---
engine = create_async_engine(
    settings.DATABASE_URL_asyncpg,
    echo=True,
    future=True,  # Совместимость с SQLAlchemy 2.x
)

# --- Фабрика асинхронных сессий ---
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# --- Базовый класс моделей ---
Base = declarative_base()


# -------------------------------------------------------------------
# Зависимость FastAPI для получения сессии
# -------------------------------------------------------------------

async def get_async_session() -> AsyncSession:
    """Асинхронная сессия для внедрения зависимостей."""
    async with AsyncSessionLocal() as session:
        yield session

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.models.user import User


# -------------------------------------------------------------------
# Менеджер пользователей
# -------------------------------------------------------------------

class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    Пользовательский менеджер для FastAPI Users.
    Использует SECRET_KEY для генерации токенов сброса и верификации.
    """
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY


# -------------------------------------------------------------------
# Зависимости для FastAPI Users
# -------------------------------------------------------------------

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Получение доступа к таблице пользователей через SQLAlchemy."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
):
    """Зависимость FastAPI для менеджера пользователей."""
    yield UserManager(user_db)


# -------------------------------------------------------------------
# JWT-аутентификация
# -------------------------------------------------------------------

bearer_transport = BearerTransport(tokenUrl="auth/login")


def get_jwt_strategy() -> JWTStrategy:
    """Формирование стратегии JWT на основе SECRET_KEY."""
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.JWT_LIFETIME_SECONDS,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# -------------------------------------------------------------------
# Основной объект FastAPIUsers и зависимости
# -------------------------------------------------------------------

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

from fastapi import APIRouter

from app.core.auth import auth_backend, fastapi_users
from app.schemas.user import UserRead, UserCreate


router = APIRouter(prefix="/auth", tags=["Авторизация"])

# -------------------------------------------------------------------
# Эндпоинты
# -------------------------------------------------------------------

# Регистрация нового пользователя
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate)
)

# Вход (аутентификация)
router.include_router(
    fastapi_users.get_auth_router(auth_backend)
)

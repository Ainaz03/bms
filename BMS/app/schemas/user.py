from typing import Optional
from fastapi_users import schemas

from app.models.user import UserRole


# -------------------------------------------------------------------
# Pydantic-схемы для пользователей
# -------------------------------------------------------------------

class UserRead(schemas.BaseUser[int]):
    """
    Ответная модель пользователя:
      - Наследует id, email, is_active, is_superuser, is_verified
      - Добавляет role и team_id
    """
    role: UserRole
    team_id: Optional[int] = None


class UserCreate(schemas.BaseUserCreate):
    """
    Модель для создания пользователя:
      - email, password
      - Опциональная роль (по умолчанию USER)
    """
    role: Optional[UserRole] = UserRole.USER


class UserUpdate(schemas.BaseUserUpdate):
    """
    Модель для обновления пользователя:
      - password, is_active, is_superuser, is_verified
      - Опциональная роль
    """
    role: Optional[UserRole] = None
    

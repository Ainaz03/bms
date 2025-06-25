from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.user import UserRole


# -------------------------------------------------------------------
# Pydantic-схемы для работы с командами
# -------------------------------------------------------------------

class TeamCreate(BaseModel):
    """
    Входная модель для создания команды.
    """
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Название команды"
    )


class TeamRead(BaseModel):
    """
    Модель для ответа с деталями команды.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    invite_code: Optional[str] = Field(
        None,
        description="Код приглашения для присоединения к команде"
    )
    admin_id: int = Field(
        ...,
        description="ID пользователя-администратора команды"
    )
    members: List[int] = Field(
        ...,
        description="Список ID участников команды"
    )


class TeamMemberAdd(BaseModel):
    """
    Входная модель для добавления пользователя в команду.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(
        ...,
        description="ID пользователя, которого нужно добавить в команду"
    )


class TeamMemberRoleUpdate(BaseModel):
    """
    Входная модель для обновления роли участника внутри команды.
    """
    model_config = ConfigDict(from_attributes=True)

    role: UserRole = Field(
        ...,
        description="Новая роль участника: MANAGER или USER"
    )

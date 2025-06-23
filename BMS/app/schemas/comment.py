from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# -------------------------------------------------------------------
# Pydantic-схемы для работы с комментариями
# -------------------------------------------------------------------

class CommentRead(BaseModel):
    """
    Модель для чтения (ответ) комментария.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Уникальный идентификатор комментария"
    )
    text: str = Field(
        ...,
        description="Текст комментария"
    )
    author_id: int = Field(
        ...,
        description="ID пользователя, который оставил комментарий"
    )
    created_at: datetime = Field(
        ...,
        description="Дата и время создания комментария"
    )


class CommentCreate(BaseModel):
    """
    Модель для создания нового комментария.
    """
    model_config = ConfigDict(from_attributes=True)

    text: str = Field(
        ...,
        description="Текст комментария"
    )

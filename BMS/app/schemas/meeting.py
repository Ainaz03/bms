from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# -------------------------------------------------------------------
# Pydantic-схемы для работы с встречами
# -------------------------------------------------------------------

class MeetingBase(BaseModel):
    """
    Общие поля для создания и обновления встречи.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Тема встречи"
    )
    start_time: datetime = Field(
        ...,
        description="Дата и время начала встречи"
    )
    end_time: datetime = Field(
        ...,
        description="Дата и время окончания встречи"
    )
    participants: List[int] = Field(
        ...,
        description="Список ID пользователей-участников встречи (включая создателя)"
    )


class MeetingCreate(MeetingBase):
    """
    Модель для создания новой встречи.
    """
    ...


class MeetingUpdate(BaseModel):
    """
    Модель для частичного обновления полей встречи.
    """
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Новая тема встречи"
    )
    start_time: Optional[datetime] = Field(
        None,
        description="Новое время начала встречи"
    )
    end_time: Optional[datetime] = Field(
        None,
        description="Новое время окончания встречи"
    )
    participants: Optional[List[int]] = Field(
        None,
        description="Обновлённый список ID участников"
    )


class MeetingRead(BaseModel):
    """
    Модель для ответа с деталями встречи.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    start_time: datetime
    end_time: datetime
    creator_id: int = Field(
        ...,
        description="ID пользователя, создавшего встречу"
    )
    participants: List[int] = Field(
        ...,
        description="Список ID участников встречи"
    )

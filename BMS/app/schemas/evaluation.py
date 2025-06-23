from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# -------------------------------------------------------------------
# Pydantic-схемы для работы с оценками
# -------------------------------------------------------------------

class EvaluationRead(BaseModel):
    """
    Модель ответа с деталями оценки.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Уникальный идентификатор оценки"
    )
    score: int = Field(
        ...,
        description="Баллы, выставленные за задачу"
    )
    evaluator_id: int = Field(
        ...,
        description="ID пользователя, который выставил оценку"
    )
    created_at: datetime = Field(
        ...,
        description="Дата и время создания оценки"
    )


class EvaluationCreate(BaseModel):
    """
    Модель для создания новой оценки задачи.
    """
    model_config = ConfigDict(from_attributes=True)

    score: int = Field(
        ...,
        ge=1,
        le=5,
        description="Оценка за задачу от 1 до 5"
    )

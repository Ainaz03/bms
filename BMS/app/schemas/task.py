from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus
from app.schemas.comment import CommentRead
from app.schemas.evaluation import EvaluationRead


# -------------------------------------------------------------------
# Базовые Pydantic-модели для задач
# -------------------------------------------------------------------

class TaskBase(BaseModel):
    """
    Общие поля задачи для создания и частичного обновления.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Краткое название задачи"
    )
    description: Optional[str] = Field(
        None,
        description="Подробное описание задачи"
    )
    deadline: Optional[datetime] = Field(
        None,
        description="Срок выполнения задачи"
    )
    assignee_id: int = Field(
        ...,
        description="ID пользователя—исполнителя задачи"
    )
    status: TaskStatus = Field(
        TaskStatus.OPEN,
        description="Статус задачи (по умолчанию открыта)"
    )


class TaskCreate(TaskBase):
    """
    Модель для создания новой задачи.
    """
    ...


class TaskUpdate(BaseModel):
    """
    Модель для обновления полей существующей задачи.
    """
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(
        None,
        description="Новое название задачи"
    )
    description: Optional[str] = Field(
        None,
        description="Новое описание задачи"
    )
    deadline: Optional[datetime] = Field(
        None,
        description="Новый срок выполнения"
    )
    assignee_id: Optional[int] = Field(
        None,
        description="ID нового исполнителя"
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="Новый статус задачи"
    )


class TaskRead(BaseModel):
    """
    Модель для ответа с полной информацией о задаче.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    creator_id: int
    assignee_id: int
    created_at: datetime
    deadline: Optional[datetime]
    comments: List[CommentRead]
    evaluations: List[EvaluationRead]

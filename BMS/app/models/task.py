import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, Integer, String, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base


# -------------------------------------------------------------------
# Перечисления
# -------------------------------------------------------------------

class TaskStatus(str, enum.Enum):
    """Возможные статусы задачи."""
    OPEN = "open"                # Открыта
    IN_PROGRESS = "in_progress"  # В работе
    DONE = "done"                # Выполнена


# -------------------------------------------------------------------
# Основная модель Task
# -------------------------------------------------------------------

class Task(Base):
    """
    Задача внутри системы.
    Хранит информацию о заголовке, описании, сроках,
    создателе, исполнителе, комментариях и оценках.
    """
    __tablename__ = 'tasks'

    # --- Базовые поля ---
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный идентификатор задачи"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Краткое название задачи"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Подробное описание задачи"
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status_enum"),
        default=TaskStatus.OPEN,
        nullable=False,
        comment="Текущий статус задачи"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Дата и время создания задачи"
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Срок выполнения задачи"
    )

    # --- Связь с пользователями ---
    creator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        comment="ID пользователя, создавшего задачу"
    )
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_tasks",
        foreign_keys=[creator_id],
    )

    assignee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        comment="ID пользователя—исполнителя задачи"
    )
    assignee: Mapped["User"] = relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assignee_id],
    )

    # --- Связанные сущности ---
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="task",
        cascade="all, delete-orphan",
    )

from datetime import datetime
from sqlalchemy import DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base


# -------------------------------------------------------------------
# Модель Evaluation
# -------------------------------------------------------------------

class Evaluation(Base):
    """
    Оценка выполненной задачи.
    Хранит балл, время создания, связана с задачей и оценившим пользователем.
    """
    __tablename__ = 'evaluations'

    # --- Базовые поля ---
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный идентификатор оценки"
    )
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Баллы, выставленные за задачу (1–5)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Дата и время создания оценки"
    )

    # --- Связь с задачей ---
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('tasks.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        comment="ID задачи, для которой выставлена оценка"
    )
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="evaluations",
    )

    # --- Связь с пользователем-оценившим ---
    evaluator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        comment="ID пользователя, который выставил оценку"
    )
    evaluator: Mapped["User"] = relationship(
        "User",
    )

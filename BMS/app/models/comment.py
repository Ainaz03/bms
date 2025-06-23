from datetime import datetime
from sqlalchemy import DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base


# -------------------------------------------------------------------
# Модель Comment
# -------------------------------------------------------------------

class Comment(Base):
    """
    Комментарий, прикреплённый к задаче.
    Содержит текст, автора и время создания.
    """
    __tablename__ = 'comments'

    # --- Базовые поля ---
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный идентификатор комментария"
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Текст комментария"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Дата и время создания комментария"
    )

    # --- Связь с задачей ---
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('tasks.id', ondelete='CASCADE'),
        nullable=False,
        comment="ID задачи, к которой относится комментарий"
    )
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="comments",
    )

    # --- Автор комментария ---
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        comment="ID пользователя-автора комментария"
    )
    author: Mapped["User"] = relationship(
        "User",
    )

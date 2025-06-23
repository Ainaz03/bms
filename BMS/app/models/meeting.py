from datetime import datetime
from typing import List
from sqlalchemy import DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from app.models.user import meeting_participants_association


# -------------------------------------------------------------------
# Модель Meeting
# -------------------------------------------------------------------

class Meeting(Base):
    """
    Встреча между пользователями.
    Содержит тему, время и список участников.
    """
    __tablename__ = 'meetings'

    # --- Основные поля ---
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный идентификатор встречи"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Тема или название встречи"
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Дата и время начала встречи"
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Дата и время окончания встречи"
    )

    # --- Создатель ---
    creator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        comment="ID пользователя, создавшего встречу"
    )
    creator: Mapped["User"] = relationship(
        "User",
        backref="created_meetings",
    )

    # --- Участники (M2M) ---
    participants: Mapped[List["User"]] = relationship(
        "User",
        secondary=meeting_participants_association,
        back_populates="meetings",
    )

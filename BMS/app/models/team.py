from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List

from app.core.database import Base


# -------------------------------------------------------------------
# Модель Team
# -------------------------------------------------------------------

class Team(Base):
    """
    Команда/компания внутри системы.
    Хранит имя, код приглашения, администратора и список участников.
    """
    __tablename__ = 'teams'

    # --- Основные поля ---
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный идентификатор команды"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Название команды"
    )
    invite_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=True,
        comment="Код приглашения для входа в команду"
    )

    # --- Администратор команды ---
    admin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        comment="ID пользователя — администратора команды"
    )
    admin: Mapped["User"] = relationship(
        "User",
        foreign_keys=[admin_id],
        backref="admin_teams",
    )

    # --- Участники команды ---
    members: Mapped[List["User"]] = relationship(
        "User",
        back_populates="team",
        foreign_keys="[User.team_id]",
    )

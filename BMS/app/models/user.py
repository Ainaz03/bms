import enum
from sqlalchemy import Column, Integer, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable

from app.core.database import Base


# -------------------------------------------------------------------
# Перечисления
# -------------------------------------------------------------------

class UserRole(str, enum.Enum):
    """Роли пользователей в системе."""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


# -------------------------------------------------------------------
# Ассоциативная таблица для связи "многие-ко-многим"
# между встречами и пользователями
# -------------------------------------------------------------------

meeting_participants_association = Table(
    'meeting_participants',
    Base.metadata,
    Column('meeting_id', Integer, ForeignKey('meetings.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
)


# -------------------------------------------------------------------
# Основная модель User
# -------------------------------------------------------------------

class User(SQLAlchemyBaseUserTable[int], Base):
    """
    Пользователь системы.
    Наследуется от SQLAlchemyBaseUserTable, который уже содержит:
      - id, email, hashed_password
      - is_active, is_superuser, is_verified
    """
    __tablename__ = 'users'

    # --- Основные поля ---
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        default=UserRole.USER,
        nullable=False,
        comment="Глобальная роль пользователя"
    )

    # --- Связь с командой ---
    team_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('teams.id', ondelete='SET NULL'),
        nullable=True,
        comment="ID команды, к которой привязан пользователь"
    )
    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="members",
        foreign_keys=[team_id]
    )

    # --- Связь с задачами ---
    created_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="creator",
        foreign_keys="Task.creator_id",
        cascade="all, delete-orphan",
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assignee_id",
    )

    # --- Связь с встречами ---
    meetings: Mapped[list["Meeting"]] = relationship(
        "Meeting",
        secondary=meeting_participants_association,
        back_populates="participants",
    )

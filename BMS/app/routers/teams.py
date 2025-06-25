from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.viewsets.TeamViewSet import TeamViewSet
from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.models.user import User
from app.schemas.team import TeamCreate, TeamRead, TeamMemberAdd, TeamMemberRoleUpdate


router = APIRouter(prefix="/teams", tags=["Команды"])

# -------------------------------------------------------------------
# Эндпоинты
# -------------------------------------------------------------------

@router.post(
    "/",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    description="Создание новой команды. Текущий пользователь становится её администратором."
)
async def create_team(
    team_in: TeamCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TeamViewSet(current_user, db)
    return await viewset.create_team(team_in)


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    description="Просмотр информации о команде по её ID (глобальные админы или админ этой команды)"
)
async def read_team(
    team_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TeamViewSet(current_user, db)
    return await viewset.read_team(team_id)


@router.post(
    "/{team_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Добавление участника в команду (глобальные админы или админ команды)"
)
async def add_member(
    team_id: int,
    member_in: TeamMemberAdd,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TeamViewSet(current_user, db)
    await viewset.add_member(team_id, member_in)


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Удаление участника из команды (глобальные админы или админ команды)"
)
async def remove_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TeamViewSet(current_user, db)
    await viewset.remove_member(team_id, user_id)


@router.patch(
    "/{team_id}/members/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Изменение роли участника (только администраторы команды или системы)"
)
async def update_member_role(
    team_id: int,
    user_id: int,
    role_in: TeamMemberRoleUpdate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    viewset = TeamViewSet(current_user, db)
    await viewset.update_member_role(team_id, user_id, role_in)
    
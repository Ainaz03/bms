from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.utils.services import assert_team_admin_or_global_admin, get_team_or_404, get_user_or_404
from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.models.team import Team
from app.models.user import User, UserRole
from app.schemas.team import TeamCreate, TeamRead, TeamMemberAdd, TeamMemberRoleUpdate
from app.utils.codegen import generate_unique_invite_code


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
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администратор системы может создавать команду")

    code = await generate_unique_invite_code(db)
    team = Team(
        name=team_in.name,
        invite_code=code,
        admin_id=current_user.id
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return TeamRead(
        id=team.id,
        name=team.name,
        invite_code=team.invite_code,
        admin_id=team.admin_id,
        members=[]
    )


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
    team = await get_team_or_404(team_id, db)
    assert_team_admin_or_global_admin(current_user, team)

    return TeamRead(
        id=team.id,
        name=team.name,
        invite_code=team.invite_code,
        admin_id=team.admin_id,
        members=[u.id for u in team.members]
    )


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
    team = await get_team_or_404(team_id, db)
    assert_team_admin_or_global_admin(current_user, team)

    user = await get_user_or_404(member_in.user_id, db)
    team.members.append(user)
    await db.commit()


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
    team = await get_team_or_404(team_id, db)
    assert_team_admin_or_global_admin(current_user, team)

    user = await get_user_or_404(user_id, db)

    if user in team.members:
        team.members.remove(user)
        await db.commit()


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
    team = await get_team_or_404(team_id, db)
    assert_team_admin_or_global_admin(current_user, team)

    user = await get_user_or_404(user_id, db)

    if user.team_id != team_id:
        raise HTTPException(status_code=400, detail="Пользователь не состоит в этой команде")

    if user.id == team.admin_id:
        raise HTTPException(status_code=400, detail="Нельзя менять роль администратора команды")

    await db.execute(
        update(User).where(User.id == user_id).values(role=role_in.role)
    )
    await db.commit()

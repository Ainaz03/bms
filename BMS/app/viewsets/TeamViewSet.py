from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.utils.services import assert_team_admin_or_global_admin, get_team_or_404, get_user_or_404
from app.models.team import Team
from app.models.user import User, UserRole
from app.schemas.team import TeamCreate, TeamRead, TeamMemberAdd, TeamMemberRoleUpdate
from app.utils.codegen import generate_unique_invite_code


class TeamViewSet:
    def __init__(self, current_user: User, db: AsyncSession):
        self.current_user = current_user
        self.db = db

    async def create_team(self, team_in: TeamCreate) -> TeamRead:
        if self.current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Только администратор системы может создавать команду")

        code = await generate_unique_invite_code(self.db)
        team = Team(
            name=team_in.name,
            invite_code=code,
            admin_id=self.current_user.id
        )
        self.db.add(team)
        await self.db.commit()
        await self.db.refresh(team)

        return TeamRead(
            id=team.id,
            name=team.name,
            invite_code=team.invite_code,
            admin_id=team.admin_id,
            members=[]
        )

    async def read_team(self, team_id: int) -> TeamRead:
        team = await get_team_or_404(team_id, self.db)
        assert_team_admin_or_global_admin(self.current_user, team)

        return TeamRead(
            id=team.id,
            name=team.name,
            invite_code=team.invite_code,
            admin_id=team.admin_id,
            members=[u.id for u in team.members]
        )

    async def add_member(self, team_id: int, member_in: TeamMemberAdd) -> None:
        team = await get_team_or_404(team_id, self.db)
        assert_team_admin_or_global_admin(self.current_user, team)

        user = await get_user_or_404(member_in.user_id, self.db)
        team.members.append(user)
        await self.db.commit()

    async def remove_member(self, team_id: int, user_id: int) -> None:
        team = await get_team_or_404(team_id, self.db)
        assert_team_admin_or_global_admin(self.current_user, team)

        user = await get_user_or_404(user_id, self.db)

        if user in team.members:
            team.members.remove(user)
            await self.db.commit()

    async def update_member_role(self, team_id: int, user_id: int, role_in: TeamMemberRoleUpdate) -> None:
        team = await get_team_or_404(team_id, self.db)
        assert_team_admin_or_global_admin(self.current_user, team)

        user = await get_user_or_404(user_id, self.db)

        if user.team_id != team_id:
            raise HTTPException(status_code=400, detail="Пользователь не состоит в этой команде")

        if user.id == team.admin_id:
            raise HTTPException(status_code=400, detail="Нельзя менять роль администратора команды")

        await self.db.execute(
            update(User).where(User.id == user_id).values(role=role_in.role)
        )
        await self.db.commit()

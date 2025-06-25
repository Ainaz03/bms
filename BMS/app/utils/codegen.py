import string
import secrets
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.team import Team


async def generate_unique_invite_code(
    db: AsyncSession,
    length: int = 8,
    alphabet: str = string.ascii_uppercase + string.digits,
) -> str:
    """
    Генерирует уникальный случайный код приглашения заданной длины.
    Проверяет уникальность кода в БД в цикле, пока не найдёт свободный.
    """
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        q = await db.execute(select(Team).where(Team.invite_code == code))
        if not q.scalars().first():
            return code

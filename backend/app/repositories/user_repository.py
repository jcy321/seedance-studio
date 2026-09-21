from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, email: str, password_hash: str, nickname: Optional[str] = None) -> User:
        return await self.create(
            email=email,
            password_hash=password_hash,
            nickname=nickname or email.split("@")[0],
            is_verified=True,
        )

    async def update_password(self, user_id: int, new_password_hash: str) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user:
            user.password_hash = new_password_hash
            await self.db.flush()
        return user

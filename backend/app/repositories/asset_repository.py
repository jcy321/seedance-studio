from typing import Optional, List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import UserAsset, AssetType
from app.repositories.base import BaseRepository


class AssetRepository(BaseRepository[UserAsset]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, UserAsset)

    async def list_by_user(
        self, user_id: int, asset_type: Optional[AssetType] = None
    ) -> List[UserAsset]:
        conditions = [UserAsset.user_id == user_id]
        if asset_type:
            conditions.append(UserAsset.asset_type == asset_type)

        result = await self.db.execute(
            select(UserAsset)
            .where(and_(*conditions))
            .order_by(UserAsset.updated_at.desc())
        )
        return list(result.scalars().all())

    async def find_match(
        self, user_id: int, original_name: str, asset_type: AssetType
    ) -> Optional[UserAsset]:
        result = await self.db.execute(
            select(UserAsset).where(
                and_(
                    UserAsset.user_id == user_id,
                    UserAsset.original_name == original_name,
                    UserAsset.asset_type == asset_type,
                )
            )
        )
        return result.scalar_one_or_none()

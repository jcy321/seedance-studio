"""资产匹配与复用服务"""
from typing import Optional, List, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import UserAsset, AssetType
from app.repositories.asset_repository import AssetRepository


class AssetService:
    def __init__(self, db: AsyncSession):
        self.repo = AssetRepository(db)

    async def match_assets(
        self, user_id: int, characters: Dict[str, Dict]
    ) -> List[Dict]:
        """匹配用户资产库，返回匹配结果"""
        results = []
        for original_name, char_info in characters.items():
            existing = await self.repo.find_match(
                user_id=user_id,
                original_name=original_name,
                asset_type=AssetType.CHARACTER,
            )
            results.append({
                "original_name": original_name,
                "alias_name": char_info.get("alias", ""),
                "status": "matched" if existing else "new",
                "asset_id": existing.id if existing else None,
                "image_url": existing.image_url if existing else None,
                "description": char_info.get("description", ""),
            })
        return results

    async def create_asset(
        self,
        user_id: int,
        asset_type: str,
        original_name: str,
        alias_name: str,
        prompt_description: str,
        image_url: str,
        gender: Optional[str] = None,
        source_project_id: Optional[int] = None,
    ) -> UserAsset:
        """创建新资产"""
        return await self.repo.create(
            user_id=user_id,
            asset_type=AssetType(asset_type),
            original_name=original_name,
            alias_name=alias_name,
            prompt_description=prompt_description,
            image_url=image_url,
            gender=gender,
            source_project_id=source_project_id,
        )

    async def get_user_assets(
        self, user_id: int, asset_type: Optional[str] = None
    ) -> List[UserAsset]:
        """获取用户资产列表"""
        type_enum = AssetType(asset_type) if asset_type else None
        return await self.repo.list_by_user(user_id, type_enum)

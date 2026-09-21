from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_settings import UserSettings


class UserSettingsRepository:
    """用户设置数据访问层"""

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: int) -> Optional[UserSettings]:
        """根据用户ID获取设置"""
        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_id: int, **kwargs) -> UserSettings:
        """创建用户设置"""
        settings = UserSettings(user_id=user_id, **kwargs)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        return settings

    @staticmethod
    async def update(
        db: AsyncSession, settings: UserSettings, **kwargs
    ) -> UserSettings:
        """更新用户设置"""
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        await db.commit()
        await db.refresh(settings)
        return settings

    @staticmethod
    async def get_or_create(db: AsyncSession, user_id: int) -> UserSettings:
        """获取或创建用户设置"""
        settings = await UserSettingsRepository.get_by_user_id(db, user_id)
        if not settings:
            settings = await UserSettingsRepository.create(db, user_id)
        return settings

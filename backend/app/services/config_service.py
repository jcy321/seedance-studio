"""配置辅助函数 - 获取用户配置"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.user_settings_repository import UserSettingsRepository


class UserConfig:
    """用户配置封装"""

    def __init__(
        self,
        llm_api_type: str,
        llm_base_url: str,
        llm_api_key: str,
        llm_model_main: str,
        llm_model_fast: str,
        seedream_api_type: str,
        seedream_base_url: str,
        seedream_api_key: str,
        seedream_model: str,
        seedance_api_type: str,
        seedance_base_url: str,
        seedance_api_key: str,
        seedance_model: str,
    ):
        self.llm_api_type = llm_api_type
        self.llm_base_url = llm_base_url
        self.llm_api_key = llm_api_key
        self.llm_model_main = llm_model_main
        self.llm_model_fast = llm_model_fast

        self.seedream_api_type = seedream_api_type
        self.seedream_base_url = seedream_base_url
        self.seedream_api_key = seedream_api_key
        self.seedream_model = seedream_model

        self.seedance_api_type = seedance_api_type
        self.seedance_base_url = seedance_base_url
        self.seedance_api_key = seedance_api_key
        self.seedance_model = seedance_model


class ConfigurationError(Exception):
    """配置错误异常"""
    pass


def _coalesce(value: Optional[str], default: str) -> str:
    if isinstance(value, str):
        value = value.strip()
    return value or default


def get_effective_config_values(user_settings=None) -> dict:
    """计算用户配置的最终生效值，未配置时回退到系统默认值。"""
    return {
        "llm_api_type": _coalesce(getattr(user_settings, "llm_api_type", None), settings.default_llm_api_type),
        "llm_base_url": _coalesce(getattr(user_settings, "llm_base_url", None), settings.default_llm_base_url),
        "llm_api_key": _coalesce(getattr(user_settings, "llm_api_key", None), settings.default_llm_api_key),
        "llm_model_main": _coalesce(getattr(user_settings, "llm_model_main", None), settings.default_llm_model_main),
        "llm_model_fast": _coalesce(getattr(user_settings, "llm_model_fast", None), settings.default_llm_model_fast),
        "seedream_api_type": _coalesce(getattr(user_settings, "seedream_api_type", None), settings.default_seedream_api_type),
        "seedream_base_url": _coalesce(getattr(user_settings, "seedream_base_url", None), settings.default_seedream_base_url),
        "seedream_api_key": _coalesce(getattr(user_settings, "seedream_api_key", None), settings.default_seedream_api_key),
        "seedream_model": _coalesce(getattr(user_settings, "seedream_model", None), settings.default_seedream_model),
        "seedance_api_type": _coalesce(getattr(user_settings, "seedance_api_type", None), settings.default_seedance_api_type),
        "seedance_base_url": _coalesce(getattr(user_settings, "seedance_base_url", None), settings.default_seedance_base_url),
        "seedance_api_key": _coalesce(getattr(user_settings, "seedance_api_key", None), settings.default_seedance_api_key),
        "seedance_model": _coalesce(getattr(user_settings, "seedance_model", None), settings.default_seedance_model),
    }


async def get_user_config(db: AsyncSession, user_id: int) -> UserConfig:
    """获取用户配置，未配置项回退到系统默认值。"""
    user_settings = await UserSettingsRepository.get_by_user_id(db, user_id)
    effective = get_effective_config_values(user_settings)

    return UserConfig(**effective)

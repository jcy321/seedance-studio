from pydantic import BaseModel, Field
from typing import Optional


class UserSettingsBase(BaseModel):
    """用户设置基础Schema"""
    llm_api_type: Optional[str] = Field(None, description="LLM API类型 (claude/openai/ark)")
    llm_base_url: Optional[str] = Field(None, description="LLM API地址")
    llm_api_key: Optional[str] = Field(None, description="LLM API密钥")
    llm_model_main: Optional[str] = Field(None, description="LLM主模型名称")
    llm_model_fast: Optional[str] = Field(None, description="LLM快速模型名称")

    seedream_api_type: Optional[str] = Field(None, description="Seedream API类型 (ark/openai)")
    seedream_base_url: Optional[str] = Field(None, description="Seedream API地址")
    seedream_api_key: Optional[str] = Field(None, description="Seedream API密钥")
    seedream_model: Optional[str] = Field(None, description="Seedream模型名称")

    seedance_api_type: Optional[str] = Field(None, description="Seedance API类型 (ark/custom)")
    seedance_base_url: Optional[str] = Field(None, description="Seedance API地址")
    seedance_api_key: Optional[str] = Field(None, description="Seedance API密钥")
    seedance_model: Optional[str] = Field(None, description="Seedance模型名称")


class UserSettingsUpdate(UserSettingsBase):
    """更新用户设置"""
    pass


class UserSettingsResponse(UserSettingsBase):
    """用户设置响应"""
    id: int
    user_id: int

    class Config:
        from_attributes = True


class UserSettingsPublic(BaseModel):
    """公开的用户设置（隐藏API密钥）"""
    id: int
    user_id: int

    llm_api_type: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_api_key_configured: bool = Field(description="是否已配置LLM API密钥")
    llm_model_main: Optional[str] = None
    llm_model_fast: Optional[str] = None

    seedream_api_type: Optional[str] = None
    seedream_base_url: Optional[str] = None
    seedream_api_key_configured: bool = Field(description="是否已配置Seedream API密钥")
    seedream_model: Optional[str] = None

    seedance_api_type: Optional[str] = None
    seedance_base_url: Optional[str] = None
    seedance_api_key_configured: bool = Field(description="是否已配置Seedance API密钥")
    seedance_model: Optional[str] = None

    class Config:
        from_attributes = True

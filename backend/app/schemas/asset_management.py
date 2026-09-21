"""资产管理相关的Schema定义"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AssetExtractionRequest(BaseModel):
    """资产提取请求"""
    pass


class AssetExtractionResponse(BaseModel):
    """资产提取响应"""
    characters_count: int
    scenes_count: int
    items_count: int
    costumes_count: int
    skipped_costumes_count: int = 0
    warnings: List[str] = []
    message: str


class SceneResponse(BaseModel):
    """场景响应"""
    id: int
    script_id: int
    name: str
    description: Optional[str] = None
    image_prompt: Optional[str] = None  # 图像提示词
    reference_image_path: Optional[str] = None
    generation_status: str
    generation_task_id: Optional[int] = None
    candidate_images_json: List[str] = []
    user_asset_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemResponse(BaseModel):
    """道具响应"""
    id: int
    script_id: int
    name: str
    description: Optional[str] = None
    image_prompt: Optional[str] = None  # 图像提示词
    reference_image_path: Optional[str] = None
    generation_status: str
    generation_task_id: Optional[int] = None
    candidate_images_json: List[str] = []
    user_asset_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CostumeResponse(BaseModel):
    """服装响应"""
    id: int
    script_id: int
    character_id: Optional[int] = None
    character_name: Optional[str] = None  # 所属角色名称
    name: str
    description: Optional[str] = None
    image_prompt: Optional[str] = None  # 图像提示词
    reference_image_path: Optional[str] = None
    generation_status: str
    generation_task_id: Optional[int] = None
    candidate_images_json: List[str] = []
    user_asset_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetPromptGenerationRequest(BaseModel):
    """资产提示词生成请求"""
    asset_type: str  # character, scene, item, costume
    asset_id: int  # 资产ID
    asset_name: str
    asset_description: str
    additional_context: Optional[str] = None


class AssetPromptGenerationResponse(BaseModel):
    """资产提示词生成响应"""
    prompt: str
    asset_type: str
    asset_name: str


class ShareAssetItem(BaseModel):
    """分享资产项"""
    asset_type: str  # character, scene, item, costume
    source_id: int  # 源资产ID


class ShareAssetsRequest(BaseModel):
    """批量分享资产请求"""
    project_id: int
    script_id: int
    items: List[ShareAssetItem]


class CreatedAssetInfo(BaseModel):
    """创建的资产信息"""
    asset_type: str
    source_id: int
    user_asset_id: int


class CreatedRelationInfo(BaseModel):
    """创建的关系信息"""
    relation_type: str
    from_asset_id: int
    to_asset_id: int


class ShareAssetsResponse(BaseModel):
    """批量分享资产响应"""
    created_assets: List[CreatedAssetInfo]
    created_relations: List[CreatedRelationInfo]
    warnings: List[str] = []
    message: str


class AssetImageSelectRequest(BaseModel):
    """资产图片选择请求"""
    image_index: int

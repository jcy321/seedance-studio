from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CharacterBase(BaseModel):
    original_name: str
    alias_name: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None


class CharacterCreate(CharacterBase):
    script_id: int


class CharacterUpdate(BaseModel):
    alias_name: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None


class CharacterResponse(CharacterBase):
    id: int
    script_id: int
    reference_prompt: Optional[str] = None  # 图像提示词
    has_reference_image: bool
    reference_image_path: Optional[str] = None
    candidate_images_json: Optional[List[str]] = None
    generation_status: str = 'pending'  # 生成状态
    user_asset_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CharacterListItem(BaseModel):
    id: int
    original_name: str
    alias_name: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    reference_prompt: Optional[str] = None  # 图像提示词
    has_reference_image: bool
    reference_image_path: Optional[str] = None
    candidate_images_json: Optional[List[str]] = None
    generation_status: str = 'pending'  # 生成状态
    user_asset_id: Optional[int] = None

    class Config:
        from_attributes = True


class CharacterImageSelectRequest(BaseModel):
    image_index: int

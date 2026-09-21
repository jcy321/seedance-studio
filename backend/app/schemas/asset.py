from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AssetCreate(BaseModel):
    asset_type: str  # character, scene, prop, clothing
    original_name: str
    prompt_description: str
    gender: Optional[str] = None
    image_url: Optional[str] = None


class AssetResponse(BaseModel):
    id: int
    asset_type: str
    original_name: str
    alias_name: str
    gender: Optional[str]
    prompt_description: str
    image_url: Optional[str]
    image_path: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class CharacterGenerationRequest(BaseModel):
    description: str
    count: int = Field(default=4, ge=1, le=4)


class CharacterGenerationResponse(BaseModel):
    images: List[str]
    task_id: str


class CharacterConfirmRequest(BaseModel):
    original_name: str
    alias_name: Optional[str] = None
    gender: Optional[str] = None
    prompt_description: str
    image_url: str
    project_id: Optional[int] = None

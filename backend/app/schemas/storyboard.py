from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class StoryboardCreate(BaseModel):
    sequence: int
    shot_type: Optional[str] = None
    shot_description: str
    dialogue: Optional[str] = None
    duration: int = Field(default=10, ge=4, le=15)
    camera_control: Optional[Dict[str, Any]] = None


class StoryboardUpdate(BaseModel):
    shot_description: Optional[str] = None
    dialogue: Optional[str] = None
    prompt_text: Optional[str] = None
    duration: Optional[int] = Field(None, ge=4, le=15)


class StoryboardResponse(BaseModel):
    id: int
    project_id: int
    sequence: int
    shot_type: Optional[str]
    shot_description: str
    dialogue: Optional[str]
    duration: int
    camera_control: Optional[Dict[str, Any]]
    prompt_text: Optional[str]
    video_url: Optional[str]
    tail_frame_path: Optional[str]
    status: str
    used_assets_json: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

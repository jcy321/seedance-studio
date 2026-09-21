from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)


class ProjectProgress(BaseModel):
    done: int = 0
    total: int = 0


class ProjectListItem(BaseModel):
    id: int
    title: str
    status: str
    progress: ProjectProgress
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    title: str
    status: str
    script_raw_text: Optional[str] = None
    docx_path: Optional[str] = None
    final_video_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    storyboard_count: int = 0

    class Config:
        from_attributes = True

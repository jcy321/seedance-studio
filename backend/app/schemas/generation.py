from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class GenerationProgress(BaseModel):
    done: int = 0
    total: int = 0
    current_scene: Optional[int] = None


class GenerationTaskItem(BaseModel):
    project_id: int
    project_title: str
    progress: GenerationProgress
    status: str
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_video_url: Optional[str] = None


class GenerationTaskList(BaseModel):
    generating: List[GenerationTaskItem] = []
    completed: List[GenerationTaskItem] = []


class GenerationStartResponse(BaseModel):
    task_id: str
    project_id: int
    status: str = "started"


class GenerationStatusResponse(BaseModel):
    task_id: str
    project_id: int
    status: str
    progress: GenerationProgress
    current_scene_info: Optional[str] = None
    error_message: Optional[str] = None

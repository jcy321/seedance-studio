"""生成任务相关的Schema定义"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class GenerationTaskResponse(BaseModel):
    """生成任务响应"""
    id: int
    task_type: str
    status: str
    progress_percent: int
    prompt: Optional[str] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerationTaskCreate(BaseModel):
    """创建生成任务请求"""
    task_type: str  # character_image, scene_image, item_image, costume_image, video
    prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GenerationTaskUpdate(BaseModel):
    """更新生成任务请求"""
    status: Optional[str] = None
    progress_percent: Optional[int] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GenerationTaskListResponse(BaseModel):
    """生成任务列表响应"""
    tasks: List[GenerationTaskResponse]
    total: int
    limit: int
    offset: int

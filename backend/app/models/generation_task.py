import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.models.base import Base


class TaskType(str, enum.Enum):
    CHARACTER_IMAGE = "character_image"
    SCENE_IMAGE = "scene_image"
    ITEM_IMAGE = "item_image"
    VIDEO = "video"


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(Enum(TaskType), nullable=False, index=True)
    target_id = Column(Integer, nullable=False)  # 关联的资产或分镜ID
    target_type = Column(String(50), nullable=False)  # character/scene/item/segment
    external_task_id = Column(String(255), index=True)  # 火山方舟返回的任务ID
    status = Column(Enum(TaskStatus), default=TaskStatus.QUEUED, nullable=False, index=True)
    progress = Column(Integer, default=0)  # 0-100
    result_url = Column(String(500))  # 生成结果URL
    thumbnail_url = Column(String(500))  # 缩略图URL
    error_message = Column(Text)
    prompt_text = Column(Text)  # 使用的提示词
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")

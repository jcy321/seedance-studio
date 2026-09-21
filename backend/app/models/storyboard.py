import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, JSON, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class SegmentStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class StoryboardSegment(Base, TimestampMixin):
    __tablename__ = "storyboard_segments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)

    shot_type = Column(String(50), nullable=True)
    shot_description = Column(Text, nullable=False)
    dialogue = Column(Text, nullable=True)
    duration = Column(Integer, default=10, nullable=False)
    camera_control = Column(JSON, nullable=True)

    # 视频提示词
    prompt_text = Column(Text, nullable=True)  # 原始提示词
    video_prompt = Column(Text, nullable=True)  # LLM生成的视频提示词
    video_prompt_edited = Column(Text, nullable=True)  # 用户编辑后的提示词

    # 生成状态
    status = Column(Enum(SegmentStatus), default=SegmentStatus.PENDING, nullable=False, index=True)
    generation_task_id = Column(String(100), nullable=True)  # 火山方舟任务ID
    generation_progress = Column(Integer, default=0)  # 生成进度 0-100
    generation_error = Column(Text, nullable=True)  # 失败原因

    # 生成结果
    video_url = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    video_thumbnail_path = Column(String(500), nullable=True)  # 视频缩略图（首帧）
    tail_frame_path = Column(String(500), nullable=True)
    tail_frame_desc = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    used_assets_json = Column(JSON, nullable=True)
    generated_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="storyboards")
    script = relationship("Script", back_populates="storyboards")

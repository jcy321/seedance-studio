from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base


class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    original_name = Column(String(255), nullable=False)
    alias_name = Column(String(100))
    gender = Column(String(20))
    description = Column(Text)

    # 人设图提示词
    reference_prompt = Column(Text)  # LLM生成的人设图提示词

    # 生成状态
    generation_status = Column(Enum(GenerationStatus), default=GenerationStatus.PENDING)
    generation_task_ids = Column(JSON)  # 4张候选图的任务ID列表
    generation_progress = Column(Integer, default=0)  # 生成进度 0-100
    generation_error = Column(Text)  # 失败原因

    # 候选图和选中图
    candidate_images_json = Column(JSON)  # 4张候选图的URL和缩略图 [{"url": "", "thumbnail_url": "", "status": ""}]
    has_reference_image = Column(Boolean, default=False)
    reference_image_path = Column(String(500))  # 选中的人设图
    selected_image_thumbnail = Column(String(500))  # 选中图的缩略图

    # 资产库关联
    user_asset_id = Column(Integer, ForeignKey("user_assets.id"))

    # 出场统计
    first_appearance_segment = Column(Integer)  # 首次出场分镜号
    total_appearances = Column(Integer, default=0)  # 总出场次数

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    script = relationship("Script", back_populates="characters")
    user_asset = relationship("UserAsset")
    costumes = relationship("Costume", back_populates="character", cascade="all, delete-orphan")

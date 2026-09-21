import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Costume(Base):
    __tablename__ = "costumes"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # 服装名称（如"银色维护服"）
    description = Column(Text)
    image_prompt = Column(Text)  # LLM生成的服装图提示词
    reference_image_path = Column(String(500))  # 生成的服装参考图路径
    reference_image_thumbnail = Column(String(500))  # 缩略图路径
    generation_status = Column(Enum(GenerationStatus), default=GenerationStatus.PENDING)
    generation_task_id = Column(String(100))  # 火山方舟任务ID
    generation_error = Column(Text)
    candidate_images_json = Column(JSON)
    user_asset_id = Column(Integer, ForeignKey("user_assets.id"))
    is_default = Column(Integer, default=0)  # 是否为默认服装
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    character = relationship("Character", back_populates="costumes")
    user_asset = relationship("UserAsset")

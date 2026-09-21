import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class SceneType(str, enum.Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"


class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    scene_type = Column(Enum(SceneType), nullable=True)
    description = Column(Text)
    image_prompt = Column(Text)  # LLM生成的场景图提示词
    candidate_images_json = Column(JSON)  # 候选图片列表
    reference_image_path = Column(String(500))  # 生成的场景参考图路径
    reference_image_thumbnail = Column(String(500))  # 缩略图路径
    generation_status = Column(Enum(GenerationStatus), default=GenerationStatus.PENDING)
    generation_task_id = Column(String(100))  # 火山方舟任务ID
    generation_error = Column(Text)
    user_asset_id = Column(Integer, ForeignKey("user_assets.id"))  # 关联到资产库
    first_appearance_segment = Column(Integer)  # 首次出场分镜号
    total_appearances = Column(Integer, default=0)  # 总出场次数
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    script = relationship("Script", back_populates="scenes")
    user_asset = relationship("UserAsset")

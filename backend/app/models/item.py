import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class ItemType(str, enum.Enum):
    PROP = "prop"  # 道具
    COSTUME = "costume"  # 服装
    OTHER = "other"


class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    item_type = Column(Enum(ItemType), default=ItemType.PROP)
    description = Column(Text)
    image_prompt = Column(Text)  # LLM生成的物品图提示词
    candidate_images_json = Column(JSON)  # 候选图片列表
    reference_image_path = Column(String(500))  # 生成的物品参考图路径
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
    script = relationship("Script", back_populates="items")
    user_asset = relationship("UserAsset")

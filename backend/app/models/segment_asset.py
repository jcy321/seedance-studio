import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class AssetType(str, enum.Enum):
    CHARACTER = "character"
    SCENE = "scene"
    ITEM = "item"
    COSTUME = "costume"


class SegmentAsset(Base):
    __tablename__ = "segment_assets"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer, ForeignKey("storyboard_segments.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    asset_id = Column(Integer, nullable=False)  # 资产ID（character_id/scene_id/item_id/costume_id）
    override_description = Column(Text)  # 覆盖描述（可选，用于特殊情况）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    segment = relationship("StoryboardSegment")

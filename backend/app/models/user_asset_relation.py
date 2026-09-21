import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship

from app.models.base import Base


class RelationType(str, enum.Enum):
    """资产关系类型"""
    BELONGS_TO_CHARACTER = "belongs_to_character"  # 服装属于角色
    # 未来可扩展：
    # BELONGS_TO_SCENE = "belongs_to_scene"  # 道具属于场景
    # DEFAULT_COSTUME = "default_costume"  # 角色的默认服装


class UserAssetRelation(Base):
    """用户资产关系表

    用于记录资产之间的关系，例如：
    - 服装属于哪个角色
    - 道具属于哪个场景
    - 角色的默认服装
    """
    __tablename__ = "user_asset_relations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    from_asset_id = Column(Integer, ForeignKey("user_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    to_asset_id = Column(Integer, ForeignKey("user_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(Enum(RelationType), nullable=False)
    source_project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"))
    source_script_id = Column(Integer, ForeignKey("scripts.id", ondelete="SET NULL"))
    metadata_json = Column(JSON)  # 额外的元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    from_asset = relationship("UserAsset", foreign_keys=[from_asset_id])
    to_asset = relationship("UserAsset", foreign_keys=[to_asset_id])

import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Index

from app.models.base import Base, TimestampMixin


class AssetType(str, enum.Enum):
    CHARACTER = "character"
    SCENE = "scene"
    PROP = "prop"
    CLOTHING = "clothing"


class UserAsset(Base, TimestampMixin):
    __tablename__ = "user_assets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)

    original_name = Column(String(255), nullable=False)
    alias_name = Column(String(100), nullable=False)
    gender = Column(String(20), nullable=True)
    prompt_description = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    image_path = Column(String(500), nullable=True)
    source_project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        Index("idx_user_asset_type_name", "user_id", "asset_type", "original_name"),
    )

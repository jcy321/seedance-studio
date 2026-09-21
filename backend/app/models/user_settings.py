from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    """用户API配置"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # LLM配置（用于拆解剧本、描述图片、判断首帧）
    llm_api_type = Column(String(50), nullable=True)  # claude, openai, ark
    llm_base_url = Column(String(500), nullable=True)
    llm_api_key = Column(String(500), nullable=True)
    llm_model_main = Column(String(200), nullable=True)  # 主模型（拆解剧本、判断首帧）
    llm_model_fast = Column(String(200), nullable=True)  # 快速模型（描述图片）

    # Seedream配置（图片生成）
    seedream_api_type = Column(String(50), nullable=True)  # ark, openai
    seedream_base_url = Column(String(500), nullable=True)
    seedream_api_key = Column(String(500), nullable=True)
    seedream_model = Column(String(200), nullable=True)

    # Seedance配置（视频生成）
    seedance_api_type = Column(String(50), nullable=True)  # ark, custom
    seedance_base_url = Column(String(500), nullable=True)
    seedance_api_key = Column(String(500), nullable=True)
    seedance_model = Column(String(200), nullable=True)

    # 关系
    user = relationship("User", backref="settings")

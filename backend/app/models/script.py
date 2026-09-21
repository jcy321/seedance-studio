import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.models.base import Base


class ScriptStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    docx_path = Column(String(500), nullable=False)
    parsing_status = Column(Enum(ScriptStatus), default=ScriptStatus.PENDING, nullable=False)
    parsing_progress = Column(Integer, default=0)
    parsing_total = Column(Integer, default=0)
    parsing_message = Column(String(500))
    parsed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="scripts")
    storyboards = relationship("StoryboardSegment", back_populates="script", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="script", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="script", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="script", cascade="all, delete-orphan")

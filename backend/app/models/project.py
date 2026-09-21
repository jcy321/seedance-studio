import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    PARSING = "parsing"
    READY = "ready"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    script_raw_text = Column(Text, nullable=True)
    docx_path = Column(String(500), nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False, index=True)
    final_video_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)

    # Relationships
    scripts = relationship("Script", back_populates="project", cascade="all, delete-orphan")
    storyboards = relationship("StoryboardSegment", back_populates="project", cascade="all, delete-orphan")

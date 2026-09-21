from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Project)

    async def list_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.updated_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Project).where(Project.user_id == user_id)
        )
        return result.scalar()

    async def get_user_project(self, project_id: int, user_id: int) -> Optional[Project]:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, project_id: int, status: ProjectStatus) -> Optional[Project]:
        project = await self.get_by_id(project_id)
        if project:
            project.status = status
            await self.db.flush()
        return project

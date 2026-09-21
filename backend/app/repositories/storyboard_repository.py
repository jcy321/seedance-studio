from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.storyboard import StoryboardSegment, SegmentStatus
from app.repositories.base import BaseRepository


class StoryboardRepository(BaseRepository[StoryboardSegment]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, StoryboardSegment)

    async def list_by_project(self, project_id: int) -> List[StoryboardSegment]:
        result = await self.db.execute(
            select(StoryboardSegment)
            .where(StoryboardSegment.project_id == project_id)
            .order_by(StoryboardSegment.sequence)
        )
        return list(result.scalars().all())

    async def list_by_script(self, script_id: int) -> List[StoryboardSegment]:
        result = await self.db.execute(
            select(StoryboardSegment)
            .where(StoryboardSegment.script_id == script_id)
            .order_by(StoryboardSegment.sequence)
        )
        return list(result.scalars().all())

    async def count_by_project(self, project_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(StoryboardSegment)
            .where(StoryboardSegment.project_id == project_id)
        )
        return result.scalar()

    async def count_completed(self, project_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(StoryboardSegment)
            .where(
                StoryboardSegment.project_id == project_id,
                StoryboardSegment.status == SegmentStatus.COMPLETED,
            )
        )
        return result.scalar()

    async def bulk_create(self, segments: List[dict]) -> List[StoryboardSegment]:
        instances = [StoryboardSegment(**s) for s in segments]
        self.db.add_all(instances)
        await self.db.flush()
        return instances

    async def update_status(
        self, segment_id: int, status: SegmentStatus, **extra
    ) -> Optional[StoryboardSegment]:
        segment = await self.get_by_id(segment_id)
        if segment:
            segment.status = status
            for k, v in extra.items():
                setattr(segment, k, v)
            await self.db.flush()
        return segment

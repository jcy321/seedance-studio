from typing import Optional, List, TypeVar, Generic, Type

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: AsyncSession, model_class: Type[ModelType]):
        self.db = db
        self.model_class = model_class

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await self.db.execute(
            select(self.model_class).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar()

    async def create(self, **kwargs) -> ModelType:
        instance = self.model_class(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def delete(self, id: int) -> bool:
        instance = await self.get_by_id(id)
        if instance:
            await self.db.delete(instance)
            return True
        return False

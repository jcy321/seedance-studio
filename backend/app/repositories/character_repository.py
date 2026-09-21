from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character


class CharacterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        script_id: int,
        original_name: str,
        alias_name: Optional[str] = None,
        gender: Optional[str] = None,
        description: Optional[str] = None
    ) -> Character:
        character = Character(
            script_id=script_id,
            original_name=original_name,
            alias_name=alias_name,
            gender=gender,
            description=description
        )
        self.db.add(character)
        await self.db.flush()
        await self.db.refresh(character)
        return character

    async def get_by_id(self, character_id: int) -> Optional[Character]:
        result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        return result.scalar_one_or_none()

    async def get_by_script(self, script_id: int) -> List[Character]:
        result = await self.db.execute(
            select(Character)
            .where(Character.script_id == script_id)
            .order_by(Character.original_name)
        )
        return list(result.scalars().all())

    async def get_characters_with_images(self, script_id: int) -> List[Character]:
        result = await self.db.execute(
            select(Character)
            .where(
                Character.script_id == script_id,
                Character.has_reference_image == True
            )
            .order_by(Character.original_name)
        )
        return list(result.scalars().all())

    async def get_characters_without_images(self, script_id: int) -> List[Character]:
        result = await self.db.execute(
            select(Character)
            .where(
                Character.script_id == script_id,
                Character.has_reference_image == False
            )
            .order_by(Character.original_name)
        )
        return list(result.scalars().all())

    async def update_candidate_images(
        self,
        character_id: int,
        images: List[str]
    ):
        character = await self.get_by_id(character_id)
        if character:
            character.candidate_images_json = images
            character.generation_status = 'completed'
            await self.db.flush()

    async def update_reference_image(
        self,
        character_id: int,
        image_path: str
    ):
        character = await self.get_by_id(character_id)
        if character:
            character.has_reference_image = True
            character.reference_image_path = image_path
            await self.db.flush()

    async def link_to_asset(
        self,
        character_id: int,
        asset_id: int
    ):
        character = await self.get_by_id(character_id)
        if character:
            character.user_asset_id = asset_id
            await self.db.flush()

    async def update(
        self,
        character_id: int,
        alias_name: Optional[str] = None,
        gender: Optional[str] = None,
        description: Optional[str] = None
    ):
        character = await self.get_by_id(character_id)
        if character:
            if alias_name is not None:
                character.alias_name = alias_name
            if gender is not None:
                character.gender = gender
            if description is not None:
                character.description = description
            await self.db.flush()

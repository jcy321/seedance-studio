from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.script import Script, ScriptStatus


class ScriptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        project_id: int,
        filename: str,
        docx_path: str
    ) -> Script:
        script = Script(
            project_id=project_id,
            filename=filename,
            docx_path=docx_path,
            parsing_status=ScriptStatus.PENDING
        )
        self.db.add(script)
        await self.db.flush()
        await self.db.refresh(script)
        return script

    async def get_by_id(self, script_id: int) -> Optional[Script]:
        result = await self.db.execute(
            select(Script).where(Script.id == script_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: int) -> List[Script]:
        result = await self.db.execute(
            select(Script)
            .where(Script.project_id == project_id)
            .order_by(Script.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_parsing_progress(
        self,
        script_id: int,
        progress: int,
        total: int,
        message: str
    ):
        script = await self.get_by_id(script_id)
        if script:
            script.parsing_progress = progress
            script.parsing_total = total
            script.parsing_message = message
            await self.db.flush()

    async def update_status(
        self,
        script_id: int,
        status: ScriptStatus,
        parsed_at: Optional[datetime] = None
    ):
        script = await self.get_by_id(script_id)
        if script:
            script.parsing_status = status
            if parsed_at:
                script.parsed_at = parsed_at
            await self.db.flush()

    async def delete(self, script_id: int):
        script = await self.get_by_id(script_id)
        if script:
            await self.db.delete(script)
            await self.db.flush()

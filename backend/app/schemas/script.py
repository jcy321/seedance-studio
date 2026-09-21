from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScriptBase(BaseModel):
    filename: str


class ScriptCreate(ScriptBase):
    pass


class ScriptUpdate(BaseModel):
    filename: Optional[str] = None


class ScriptResponse(ScriptBase):
    id: int
    project_id: int
    docx_path: str
    parsing_status: str
    parsing_progress: int
    parsing_total: int
    parsing_message: Optional[str] = None
    parsed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScriptListItem(BaseModel):
    id: int
    filename: str
    parsing_status: str
    parsing_progress: int
    parsing_total: int
    parsing_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

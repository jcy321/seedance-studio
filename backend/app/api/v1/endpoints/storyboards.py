from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.script_repository import ScriptRepository
from app.repositories.storyboard_repository import StoryboardRepository
from app.schemas.storyboard import StoryboardUpdate, StoryboardResponse

router = APIRouter(tags=["分镜管理"])


@router.get("/projects/{project_id}/storyboards", response_model=List[StoryboardResponse])
async def list_storyboards(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目的所有分镜（兼容旧接口）"""
    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="剧本不存在")

    sb_repo = StoryboardRepository(db)
    segments = await sb_repo.list_by_project(project_id)

    return [
        StoryboardResponse(
            id=s.id,
            project_id=s.project_id,
            sequence=s.sequence,
            shot_type=s.shot_type,
            shot_description=s.shot_description,
            dialogue=s.dialogue,
            duration=s.duration,
            camera_control=s.camera_control,
            prompt_text=s.prompt_text,
            video_url=s.video_url,
            tail_frame_path=s.tail_frame_path,
            status=s.status.value,
            used_assets_json=s.used_assets_json,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in segments
    ]


@router.get("/scripts/{script_id}/storyboards", response_model=List[StoryboardResponse])
async def list_storyboards_by_script(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取脚本的所有分镜"""
    script_repo = ScriptRepository(db)
    script = await script_repo.get_by_id(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 验证用户有权限
    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(script.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="无权访问此脚本")

    sb_repo = StoryboardRepository(db)
    segments = await sb_repo.list_by_script(script_id)

    return [
        StoryboardResponse(
            id=s.id,
            project_id=s.project_id,
            sequence=s.sequence,
            shot_type=s.shot_type,
            shot_description=s.shot_description,
            dialogue=s.dialogue,
            duration=s.duration,
            camera_control=s.camera_control,
            prompt_text=s.prompt_text,
            video_url=s.video_url,
            tail_frame_path=s.tail_frame_path,
            status=s.status.value,
            used_assets_json=s.used_assets_json,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in segments
    ]


@router.get("/storyboards/{segment_id}", response_model=StoryboardResponse)
async def get_storyboard(
    segment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sb_repo = StoryboardRepository(db)
    segment = await sb_repo.get_by_id(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="分镜不存在")

    # 验证归属
    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(segment.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="分镜不存在")

    return StoryboardResponse(
        id=segment.id,
        project_id=segment.project_id,
        sequence=segment.sequence,
        shot_type=segment.shot_type,
        shot_description=segment.shot_description,
        dialogue=segment.dialogue,
        duration=segment.duration,
        camera_control=segment.camera_control,
        prompt_text=segment.prompt_text,
        video_url=segment.video_url,
        tail_frame_path=segment.tail_frame_path,
        status=segment.status.value,
        used_assets_json=segment.used_assets_json,
        created_at=segment.created_at,
        updated_at=segment.updated_at,
    )


@router.put("/storyboards/{segment_id}", response_model=StoryboardResponse)
async def update_storyboard(
    segment_id: int,
    req: StoryboardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sb_repo = StoryboardRepository(db)
    segment = await sb_repo.get_by_id(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="分镜不存在")

    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(segment.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="分镜不存在")

    if req.shot_description is not None:
        segment.shot_description = req.shot_description
    if req.dialogue is not None:
        segment.dialogue = req.dialogue
    if req.prompt_text is not None:
        segment.prompt_text = req.prompt_text
    if req.duration is not None:
        segment.duration = req.duration
    await db.flush()

    return StoryboardResponse(
        id=segment.id,
        project_id=segment.project_id,
        sequence=segment.sequence,
        shot_type=segment.shot_type,
        shot_description=segment.shot_description,
        dialogue=segment.dialogue,
        duration=segment.duration,
        camera_control=segment.camera_control,
        prompt_text=segment.prompt_text,
        video_url=segment.video_url,
        tail_frame_path=segment.tail_frame_path,
        status=segment.status.value,
        used_assets_json=segment.used_assets_json,
        created_at=segment.created_at,
        updated_at=segment.updated_at,
    )

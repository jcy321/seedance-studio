from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.storyboard import StoryboardSegment, SegmentStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.storyboard_repository import StoryboardRepository
from app.repositories.asset_repository import AssetRepository
from app.schemas.generation import (
    GenerationTaskList,
    GenerationTaskItem,
    GenerationProgress,
    GenerationStartResponse,
    GenerationStatusResponse,
)
from app.services.seedance_service import SeedanceService
from app.services.llm_service import LLMService
from app.services.video_service import VideoService
from app.services.task_service import TaskService
from app.services.config_service import get_user_config, ConfigurationError
from app.core.config import settings

router = APIRouter(prefix="/generation", tags=["视频生成"])

task_service = TaskService()


@router.post("/project/{project_id}/start", response_model=GenerationStartResponse)
async def start_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 检查用户配置
    try:
        await get_user_config(db, current_user.id)
    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="剧本不存在")

    if project.status in (ProjectStatus.GENERATING, ProjectStatus.PARSING):
        raise HTTPException(status_code=400, detail="该项目正在处理中")

    sb_repo = StoryboardRepository(db)
    segments = await sb_repo.list_by_project(project_id)
    if not segments:
        raise HTTPException(status_code=400, detail="没有分镜可生成")

    project.status = ProjectStatus.GENERATING
    await db.flush()

    task = task_service.create_task(project_id, current_user.id, len(segments))
    background_tasks.add_task(
        _run_generation,
        task_id=task.task_id,
        project_id=project_id,
        user_id=current_user.id,
        db_session=db,
    )

    return GenerationStartResponse(
        task_id=task.task_id,
        project_id=project_id,
        status="started",
    )


@router.get("/tasks", response_model=GenerationTaskList)
async def get_task_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await task_service.get_user_tasks(current_user.id, db)


@router.get("/tasks/{task_id}", response_model=GenerationStatusResponse)
async def get_task_status(task_id: str):
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return GenerationStatusResponse(
        task_id=task.task_id,
        project_id=task.project_id,
        status=task.status,
        progress=GenerationProgress(**task.progress),
        error_message=task.error_message,
    )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    if task_service.cancel_task(task_id):
        return {"message": "任务已取消", "task_id": task_id}
    raise HTTPException(status_code=400, detail="任务无法取消（不存在或已完成）")


async def _run_generation(
    task_id: str,
    project_id: int,
    user_id: int,
    db_session: AsyncSession,
):
    """后台生成任务"""
    async with db_session as db:
        try:
            # 获取用户配置
            user_config = await get_user_config(db, user_id)

            sb_repo = StoryboardRepository(db)
            proj_repo = ProjectRepository(db)
            seedance = SeedanceService(user_config)
            llm = LLMService(user_config)
            video_svc = VideoService()

            segments = await sb_repo.list_by_project(project_id)
            project = await proj_repo.get_by_id(project_id)

            for idx, segment in enumerate(segments):
                if task_service.get_task(task_id) and task_service.get_task(task_id).status == "cancelled":
                    project.status = ProjectStatus.READY
                    return

                task_service.update_progress(task_id, idx, current_scene=segment.sequence)

                segment.status = SegmentStatus.GENERATING
                await db.flush()

                try:
                    prompt = segment.prompt_text or segment.shot_description
                    video_url = await seedance.generate_video(prompt=prompt, duration=segment.duration)

                    segment.status = SegmentStatus.COMPLETED
                    segment.video_url = video_url
                    await db.flush()
                except Exception as e:
                    segment.status = SegmentStatus.FAILED
                    segment.error_message = str(e)
                    await db.flush()

            # 更新项目状态
            project.status = ProjectStatus.COMPLETED
            task_service.complete_task(task_id)
            await db.flush()
        except ConfigurationError as e:
            task_service.fail_task(task_id, f"配置错误: {str(e)}")
            try:
                proj_repo = ProjectRepository(db)
                project = await proj_repo.get_by_id(project_id)
                if project:
                    project.status = ProjectStatus.FAILED
                    project.error_message = f"配置错误: {str(e)}"
                    await db.flush()
            except Exception:
                pass
        except Exception as e:
            task_service.fail_task(task_id, str(e))
            try:
                proj_repo = ProjectRepository(db)
                project = await proj_repo.get_by_id(project_id)
                if project:
                    project.status = ProjectStatus.FAILED
                    project.error_message = str(e)
                    await db.flush()
            except Exception:
                pass

"""生成任务管理API端点"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models import GenerationTask, GenerationStatus, Character, Scene, Item, Costume, StoryboardSegment, Script, Project
from app.schemas.generation_task import (
    GenerationTaskResponse,
    GenerationTaskCreate,
    GenerationTaskUpdate,
    GenerationTaskListResponse,
)
from app.services.llm_service import LLMService
from app.services.config_service import get_user_config, ConfigurationError

router = APIRouter(prefix="/generation-tasks", tags=["生成任务管理"])


@router.get("", response_model=GenerationTaskListResponse)
async def list_generation_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取生成任务列表"""
    query = select(GenerationTask).order_by(GenerationTask.created_at.desc())

    if status:
        try:
            status_enum = GenerationStatus(status)
            query = query.where(GenerationTask.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

    if task_type:
        query = query.where(GenerationTask.task_type == task_type)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    tasks = result.scalars().all()

    # 获取总数
    count_query = select(GenerationTask)
    if status:
        count_query = count_query.where(GenerationTask.status == GenerationStatus(status))
    if task_type:
        count_query = count_query.where(GenerationTask.task_type == task_type)

    from sqlalchemy import func
    count_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
    total = count_result.scalar()

    return GenerationTaskListResponse(
        tasks=[
            GenerationTaskResponse(
                id=t.id,
                task_type=t.task_type,
                status=t.status.value,
                progress_percent=t.progress_percent,
                prompt=t.prompt,
                result_url=t.result_url,
                error_message=t.error_message,
                metadata=t.metadata_json or {},
                created_at=t.created_at,
                updated_at=t.updated_at,
                completed_at=t.completed_at,
            )
            for t in tasks
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=GenerationTaskResponse)
async def get_generation_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个生成任务详情"""
    result = await db.execute(
        select(GenerationTask).where(GenerationTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return GenerationTaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status.value,
        progress_percent=task.progress_percent,
        prompt=task.prompt,
        result_url=task.result_url,
        error_message=task.error_message,
        metadata=task.metadata_json or {},
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


@router.post("", response_model=GenerationTaskResponse, status_code=201)
async def create_generation_task(
    req: GenerationTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建生成任务"""
    task = GenerationTask(
        task_type=req.task_type,
        status=GenerationStatus.PENDING,
        progress_percent=0,
        prompt=req.prompt,
        metadata_json=req.metadata or {},
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    return GenerationTaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status.value,
        progress_percent=task.progress_percent,
        prompt=task.prompt,
        result_url=task.result_url,
        error_message=task.error_message,
        metadata=task.metadata_json or {},
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


@router.patch("/{task_id}", response_model=GenerationTaskResponse)
async def update_generation_task(
    task_id: int,
    req: GenerationTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新生成任务状态"""
    result = await db.execute(
        select(GenerationTask).where(GenerationTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 更新字段
    if req.status is not None:
        try:
            task.status = GenerationStatus(req.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {req.status}")

    if req.progress_percent is not None:
        task.progress_percent = req.progress_percent

    if req.result_url is not None:
        task.result_url = req.result_url

    if req.error_message is not None:
        task.error_message = req.error_message

    if req.metadata is not None:
        task.metadata_json = req.metadata

    # 如果状态变为completed或failed，设置完成时间
    if req.status in ["completed", "failed"]:
        from datetime import datetime
        task.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    return GenerationTaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status.value,
        progress_percent=task.progress_percent,
        prompt=task.prompt,
        result_url=task.result_url,
        error_message=task.error_message,
        metadata=task.metadata_json or {},
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


@router.delete("/{task_id}", status_code=204)
async def delete_generation_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除生成任务"""
    result = await db.execute(
        select(GenerationTask).where(GenerationTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/start", response_model=GenerationTaskResponse)
async def start_generation_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """启动生成任务"""
    result = await db.execute(
        select(GenerationTask).where(GenerationTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != GenerationStatus.PENDING:
        raise HTTPException(status_code=400, detail="任务已经启动或已完成")

    # 更新任务状态为generating
    task.status = GenerationStatus.GENERATING
    task.progress_percent = 0
    await db.commit()

    # 在后台执行生成任务
    background_tasks.add_task(_execute_generation_task, task_id, db)

    await db.refresh(task)
    return GenerationTaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status.value,
        progress_percent=task.progress_percent,
        prompt=task.prompt,
        result_url=task.result_url,
        error_message=task.error_message,
        metadata=task.metadata_json or {},
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


async def _execute_generation_task(task_id: int, db: AsyncSession):
    """后台执行生成任务"""
    from datetime import datetime
    import os

    async with db as session:
        try:
            # 获取任务
            result = await session.execute(
                select(GenerationTask).where(GenerationTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                return

            # 获取target_id
            target_id = task.metadata_json.get('target_id') if task.metadata_json else None
            if not target_id:
                task.status = GenerationStatus.FAILED
                task.error_message = "缺少target_id"
                task.completed_at = datetime.utcnow()
                await session.commit()
                return

            # 获取提示词
            prompt = task.prompt
            if not prompt:
                task.status = GenerationStatus.FAILED
                task.error_message = "缺少提示词"
                task.completed_at = datetime.utcnow()
                await session.commit()
                return

            # 获取用户配置（从任务关联的资产获取用户ID）
            user_id = None
            if task.task_type == 'scene_image':
                scene_result = await session.execute(
                    select(Scene).where(Scene.id == target_id)
                )
                scene = scene_result.scalar_one_or_none()
                if scene:
                    script_result = await session.execute(
                        select(Script).where(Script.id == scene.script_id)
                    )
                    script = script_result.scalar_one_or_none()
                    if script:
                        project_result = await session.execute(
                            select(Project).where(Project.id == script.project_id)
                        )
                        project = project_result.scalar_one_or_none()
                        if project:
                            user_id = project.user_id

            if not user_id:
                task.status = GenerationStatus.FAILED
                task.error_message = "无法获取用户信息"
                task.completed_at = datetime.utcnow()
                await session.commit()
                return

            # 获取用户配置
            from app.services.config_service import get_user_config
            user_config = await get_user_config(session, user_id)

            # 调用火山方舟API生成图片
            from app.services.volcano_ark_service import VolcanoArkImageService
            from app.core.config import settings

            image_service = VolcanoArkImageService(user_config)

            # 生成4张候选图
            candidate_images = await image_service.generate_images(
                prompt=prompt,
                size="2K",
                output_format="png",
                watermark=False,
                num_images=4
            )

            # 下载图片到本地作为备份
            asset_type = task.task_type.replace('_image', '')  # scene_image -> scene
            image_dir = os.path.join(settings.image_path, f"{asset_type}s", str(target_id))
            os.makedirs(image_dir, exist_ok=True)

            for idx, url in enumerate(candidate_images):
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"candidate_{timestamp}_{idx}.png"
                local_path = os.path.join(image_dir, filename)

                try:
                    await image_service.download_image(url, local_path)
                except Exception as e:
                    print(f"下载图片失败: {e}")

            # 根据任务类型更新对应的资产
            if task.task_type == 'scene_image':
                scene_result = await session.execute(
                    select(Scene).where(Scene.id == target_id)
                )
                scene = scene_result.scalar_one_or_none()
                if scene:
                    scene.candidate_images_json = candidate_images
                    scene.generation_status = GenerationStatus.COMPLETED
            elif task.task_type == 'item_image':
                item_result = await session.execute(
                    select(Item).where(Item.id == target_id)
                )
                item = item_result.scalar_one_or_none()
                if item:
                    item.candidate_images_json = candidate_images
                    item.generation_status = GenerationStatus.COMPLETED
            elif task.task_type == 'costume_image':
                costume_result = await session.execute(
                    select(Costume).where(Costume.id == target_id)
                )
                costume = costume_result.scalar_one_or_none()
                if costume:
                    costume.candidate_images_json = candidate_images
                    costume.generation_status = GenerationStatus.COMPLETED

            # 更新任务状态
            task.status = GenerationStatus.COMPLETED
            task.progress_percent = 100
            task.completed_at = datetime.utcnow()
            task.metadata_json = {**(task.metadata_json or {}), 'candidate_images': candidate_images}

            await session.commit()

        except Exception as e:
            # 更新任务为失败状态
            try:
                result = await session.execute(
                    select(GenerationTask).where(GenerationTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                if task:
                    task.status = GenerationStatus.FAILED
                    task.error_message = str(e)
                    task.completed_at = datetime.utcnow()
                    await session.commit()
            except Exception:
                pass

import os
import uuid
import asyncio
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db, async_session_factory
from app.models.user import User
from app.models.project import ProjectStatus
from app.models.storyboard import StoryboardSegment, SegmentStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.storyboard_repository import StoryboardRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListItem,
    ProjectProgress,
)
from app.core.config import settings
from app.services.docx_parser import DocxParserService
from app.services.llm_service import LLMService
from app.services.config_service import get_user_config

router = APIRouter(prefix="/projects", tags=["剧本管理"])

# 全局进度追踪字典
parsing_progress = {}


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    req: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)
    project = await repo.create(
        user_id=current_user.id,
        title=req.title,
    )
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        status=project.status.value,
        storyboard_count=0,
    )


@router.get("", response_model=List[ProjectListItem])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)
    sb_repo = StoryboardRepository(db)
    projects = await repo.list_by_user(current_user.id)

    result = []
    for p in projects:
        total = await sb_repo.count_by_project(p.id)
        done = await sb_repo.count_completed(p.id)
        result.append(ProjectListItem(
            id=p.id,
            title=p.title,
            status=p.status.value,
            progress=ProjectProgress(done=done, total=total),
            updated_at=p.updated_at,
        ))
    return result


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)
    project = await repo.get_user_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="剧本不存在")

    sb_repo = StoryboardRepository(db)
    count = await sb_repo.count_by_project(project_id)

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        status=project.status.value,
        script_raw_text=project.script_raw_text,
        docx_path=project.docx_path,
        final_video_url=project.final_video_url,
        error_message=project.error_message,
        started_at=project.started_at,
        completed_at=project.completed_at,
        created_at=project.created_at,
        updated_at=project.updated_at,
        storyboard_count=count,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    req: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)
    project = await repo.get_user_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="剧本不存在")

    if req.title is not None:
        project.title = req.title
    await db.flush()

    sb_repo = StoryboardRepository(db)
    count = await sb_repo.count_by_project(project_id)

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        status=project.status.value,
        script_raw_text=project.script_raw_text,
        final_video_url=project.final_video_url,
        storyboard_count=count,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)
    project = await repo.get_user_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="剧本不存在")

    await repo.delete(project_id)


@router.post("/{project_id}/upload-docx")
async def upload_docx(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)
    project = await repo.get_user_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="剧本不存在")

    if not file.filename.endswith((".docx", ".doc")):
        raise HTTPException(status_code=400, detail="仅支持 .docx 或 .doc 格式")

    # 保存文件
    upload_dir = Path(settings.upload_path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = upload_dir / filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    project.docx_path = str(file_path)
    project.status = ProjectStatus.PARSING
    await db.commit()

    # 触发后台解析任务
    background_tasks.add_task(_parse_docx_background, project_id, str(file_path), current_user.id)

    return {"message": "文件上传成功，开始解析", "file_path": str(file_path)}


@router.get("/{project_id}/parsing-progress")
async def get_parsing_progress(
    project_id: int,
    current_user: User = Depends(get_current_user),
):
    """获取解析进度"""
    progress = parsing_progress.get(project_id, {
        "status": "idle",
        "progress": 0,
        "message": "等待开始",
        "total_shots": 0,
        "processed_shots": 0
    })
    return progress


async def _parse_docx_background(project_id: int, file_path: str, user_id: int):
    """后台解析docx文件"""
    try:
        # 初始化进度
        parsing_progress[project_id] = {
            "status": "parsing",
            "progress": 5,
            "message": "正在读取文件...",
            "total_shots": 0,
            "processed_shots": 0
        }

        await asyncio.sleep(0.5)  # 模拟读取时间

        # 解析docx
        parsing_progress[project_id].update({
            "progress": 15,
            "message": "正在解析表格结构..."
        })

        parser = DocxParserService()
        scenes = parser.parse_docx(file_path)

        total_shots = len(scenes)
        parsing_progress[project_id].update({
            "progress": 25,
            "message": f"发现 {total_shots} 个分镜，开始生成提示词...",
            "total_shots": total_shots
        })

        await asyncio.sleep(0.3)

        # 创建数据库会话
        async with async_session_factory() as db:
            repo = StoryboardRepository(db)

            # 获取用户配置
            try:
                user_config = await get_user_config(user_id, db)
                llm_service = LLMService(user_config)
            except Exception as e:
                # 如果用户未配置API，跳过LLM生成
                llm_service = None
                parsing_progress[project_id].update({
                    "message": f"未配置API，跳过提示词生成..."
                })

            # 保存分镜
            for idx, scene in enumerate(scenes):
                shot_number = scene.get("镜号", f"{idx+1}")
                shot_content = scene.get("镜头内容", "")
                dialogue = scene.get("台词", "")
                duration = scene.get("时长", "5")

                # 生成提示词
                prompt_text = ""
                if llm_service and shot_content:
                    try:
                        prompt_text = await llm_service.generate_prompt(
                            shot_description=shot_content,
                            dialogue=dialogue,
                            use_haiku=True
                        )
                    except:
                        prompt_text = shot_content  # 失败时使用原始描述
                else:
                    prompt_text = shot_content

                # 保存到数据库
                segment = StoryboardSegment(
                    project_id=project_id,
                    sequence=idx + 1,
                    shot_type=shot_number,
                    shot_description=shot_content,
                    dialogue=dialogue,
                    duration=int(duration) if duration.isdigit() else 5,
                    prompt_text=prompt_text,
                    status=SegmentStatus.PENDING
                )
                db.add(segment)

                # 更新进度
                processed = idx + 1
                progress_pct = 25 + int((processed / total_shots) * 70)
                parsing_progress[project_id].update({
                    "progress": progress_pct,
                    "message": f"正在处理分镜 {processed}/{total_shots}...",
                    "processed_shots": processed
                })

                await db.commit()
                await asyncio.sleep(0.1)  # 避免过快

            # 更新项目状态
            proj_repo = ProjectRepository(db)
            project = await proj_repo.get_by_id(project_id)
            if project:
                project.status = ProjectStatus.READY
                await db.commit()

        # 完成
        parsing_progress[project_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"解析完成，共 {total_shots} 个分镜"
        })

        # 5秒后清理进度数据
        await asyncio.sleep(5)
        if project_id in parsing_progress:
            del parsing_progress[project_id]

    except Exception as e:
        parsing_progress[project_id] = {
            "status": "error",
            "progress": 0,
            "message": f"解析失败: {str(e)}",
            "total_shots": 0,
            "processed_shots": 0
        }

        # 更新项目状态为失败
        try:
            async with async_session_factory() as db:
                proj_repo = ProjectRepository(db)
                project = await proj_repo.get_by_id(project_id)
                if project:
                    project.status = ProjectStatus.DRAFT
                    await db.commit()
        except:
            pass


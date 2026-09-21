import os
import uuid
import asyncio
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db, async_session_factory
from app.models.user import User
from app.models.script import ScriptStatus
from app.models.storyboard import StoryboardSegment, SegmentStatus
from app.models.character import Character
from app.repositories.script_repository import ScriptRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.storyboard_repository import StoryboardRepository
from app.repositories.character_repository import CharacterRepository
from app.schemas.script import ScriptResponse, ScriptListItem
from app.core.config import settings
from app.services.docx_parser import DocxParserService
from app.services.llm_service import LLMService
from app.services.config_service import get_user_config

router = APIRouter(prefix="/scripts", tags=["脚本管理"])

# 全局进度追踪字典
parsing_progress = {}


async def _ensure_project_scripts(
    db: AsyncSession,
    project,
) -> List:
    """兼容旧项目：补建缺失的 script 记录并修复分镜关联。"""
    script_repo = ScriptRepository(db)
    scripts = await script_repo.get_by_project(project.id)

    if not scripts and getattr(project, "docx_path", None):
        legacy_filename = Path(project.docx_path).name
        if "_" in legacy_filename:
            legacy_filename = legacy_filename.split("_", 1)[1]

        script = await script_repo.create(
            project_id=project.id,
            filename=legacy_filename,
            docx_path=project.docx_path,
        )
        await db.commit()
        scripts = [script]

    if scripts:
        latest_script_id = scripts[0].id
        await db.execute(
            update(StoryboardSegment)
            .where(
                StoryboardSegment.project_id == project.id,
                StoryboardSegment.script_id.is_(None),
            )
            .values(script_id=latest_script_id)
        )
        await db.commit()

    return scripts


@router.post("/projects/{project_id}/upload", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def upload_script(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传脚本文档到项目"""
    # 验证项目存在且属于当前用户
    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

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

    # 创建Script记录
    script_repo = ScriptRepository(db)
    script = await script_repo.create(
        project_id=project_id,
        filename=file.filename,
        docx_path=str(file_path)
    )
    await db.commit()

    # 触发后台解析任务
    background_tasks.add_task(_parse_docx_background, script.id, str(file_path), current_user.id)

    return script


@router.get("/projects/{project_id}/list", response_model=List[ScriptListItem])
async def list_scripts(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目下的所有脚本"""
    # 验证项目存在且属于当前用户
    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    scripts = await _ensure_project_scripts(db, project)

    return scripts


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取脚本详情"""
    script_repo = ScriptRepository(db)
    script = await script_repo.get_by_id(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 验证项目属于当前用户
    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(script.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="无权访问此脚本")

    return script


@router.get("/{script_id}/parsing-progress")
async def get_parsing_progress(
    script_id: int,
    current_user: User = Depends(get_current_user),
):
    """获取脚本解析进度"""
    progress = parsing_progress.get(script_id, {
        "status": "idle",
        "progress": 0,
        "message": "等待开始",
        "total_shots": 0,
        "processed_shots": 0
    })
    return progress


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除脚本"""
    script_repo = ScriptRepository(db)
    script = await script_repo.get_by_id(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 验证项目属于当前用户
    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(script.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="无权访问此脚本")

    await script_repo.delete(script_id)
    await db.commit()


async def _parse_docx_background(script_id: int, file_path: str, user_id: int):
    """后台解析docx文件"""
    try:
        # 初始化进度
        parsing_progress[script_id] = {
            "status": "parsing",
            "progress": 5,
            "message": "正在读取文件...",
            "total_shots": 0,
            "processed_shots": 0
        }

        await asyncio.sleep(0.5)

        # 解析docx
        parsing_progress[script_id].update({
            "progress": 15,
            "message": "正在解析表格结构..."
        })

        parser = DocxParserService()
        scenes = parser.parse_docx(file_path)

        total_shots = len(scenes)
        parsing_progress[script_id].update({
            "progress": 25,
            "message": f"发现 {total_shots} 个分镜，开始生成提示词...",
            "total_shots": total_shots
        })

        await asyncio.sleep(0.3)

        # 创建数据库会话
        async with async_session_factory() as db:
            script_repo = ScriptRepository(db)
            sb_repo = StoryboardRepository(db)
            char_repo = CharacterRepository(db)

            # 获取script信息
            script = await script_repo.get_by_id(script_id)
            if not script:
                raise Exception("脚本不存在")

            # 获取用户配置
            try:
                user_config = await get_user_config(user_id, db)
                llm_service = LLMService(user_config)
            except Exception:
                llm_service = None
                parsing_progress[script_id].update({
                    "message": f"未配置API，跳过提示词生成..."
                })

            # 提取角色信息
            characters_dict = {}
            for scene in scenes:
                dialogue = scene.get("台词", "")
                if dialogue and ":" in dialogue:
                    char_name = dialogue.split(":")[0].strip()
                    if char_name and char_name not in characters_dict:
                        characters_dict[char_name] = {
                            "original_name": char_name,
                            "alias_name": None,
                            "gender": None,
                            "description": None
                        }

            # 保存角色
            for char_data in characters_dict.values():
                await char_repo.create(
                    script_id=script_id,
                    original_name=char_data["original_name"],
                    alias_name=char_data["alias_name"],
                    gender=char_data["gender"],
                    description=char_data["description"]
                )
            await db.commit()

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
                        prompt_text = shot_content
                else:
                    prompt_text = shot_content

                # 保存到数据库
                segment = StoryboardSegment(
                    project_id=script.project_id,
                    script_id=script_id,
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
                parsing_progress[script_id].update({
                    "progress": progress_pct,
                    "message": f"正在处理分镜 {processed}/{total_shots}...",
                    "processed_shots": processed
                })

                await db.commit()
                await asyncio.sleep(0.1)

            # 更新脚本状态
            await script_repo.update_status(script_id, ScriptStatus.COMPLETED)
            await db.commit()

        # 完成
        parsing_progress[script_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"解析完成，共 {total_shots} 个分镜"
        })

        # 5秒后清理进度数据
        await asyncio.sleep(5)
        if script_id in parsing_progress:
            del parsing_progress[script_id]

    except Exception as e:
        parsing_progress[script_id] = {
            "status": "error",
            "progress": 0,
            "message": f"解析失败: {str(e)}",
            "total_shots": 0,
            "processed_shots": 0
        }

        # 更新脚本状态为失败
        try:
            async with async_session_factory() as db:
                script_repo = ScriptRepository(db)
                await script_repo.update_status(script_id, ScriptStatus.FAILED)
                await db.commit()
        except:
            pass

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models import GenerationStatus
from app.repositories.character_repository import CharacterRepository
from app.repositories.script_repository import ScriptRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.character import (
    CharacterResponse,
    CharacterListItem,
    CharacterUpdate,
    CharacterImageSelectRequest
)

router = APIRouter(prefix="/characters", tags=["角色管理"])


@router.get("/scripts/{script_id}/list", response_model=List[CharacterListItem])
async def list_characters(
    script_id: int,
    filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取脚本的角色列表

    filter: all | with_image | without_image
    """
    # 验证脚本存在且用户有权限
    script_repo = ScriptRepository(db)
    script = await script_repo.get_by_id(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(script.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="无权访问此脚本")

    char_repo = CharacterRepository(db)

    if filter == "with_image":
        characters = await char_repo.get_characters_with_images(script_id)
    elif filter == "without_image":
        characters = await char_repo.get_characters_without_images(script_id)
    else:
        characters = await char_repo.get_by_script(script_id)

    return characters


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取角色详情"""
    char_repo = CharacterRepository(db)
    character = await char_repo.get_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 验证用户有权限
    script_repo = ScriptRepository(db)
    script = await script_repo.get_by_id(character.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(script.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="无权访问此角色")

    return character


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    req: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新角色信息"""
    char_repo = CharacterRepository(db)
    character = await char_repo.get_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 验证用户有权限
    script_repo = ScriptRepository(db)
    script = await script_repo.get_by_id(character.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(script.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="无权访问此角色")

    # 更新角色
    await char_repo.update(
        character_id=character_id,
        alias_name=req.alias_name,
        gender=req.gender,
        description=req.description
    )
    await db.commit()

    # 重新获取更新后的角色
    character = await char_repo.get_by_id(character_id)
    return character


@router.post("/{character_id}/generate-images")
async def generate_character_images(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为角色生成人设图（4张候选）"""
    char_repo = CharacterRepository(db)
    character = await char_repo.get_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 验证用户有权限
    script_repo = ScriptRepository(db)
    script = await script_repo.get_by_id(character.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(script.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="无权访问此角色")

    # 检查是否有提示词
    if not character.reference_prompt:
        raise HTTPException(status_code=400, detail="请先生成提示词")

    # 更新状态为生成中
    character.generation_status = GenerationStatus.GENERATING
    await db.commit()

    try:
        # 获取用户配置
        from app.services.config_service import get_user_config
        user_config = await get_user_config(db, current_user.id)

        # 调用火山方舟API生成图片
        from app.services.volcano_ark_service import VolcanoArkImageService
        image_service = VolcanoArkImageService(user_config)

        # 生成4张候选图
        candidate_images = await image_service.generate_images(
            prompt=character.reference_prompt,
            size="2K",
            output_format="png",
            watermark=False,
            num_images=4
        )

        # 下载图片到本地作为备份
        from app.core.config import settings
        import os
        from datetime import datetime

        local_images = []
        image_dir = os.path.join(settings.image_path, "characters", str(character_id))
        os.makedirs(image_dir, exist_ok=True)

        for idx, url in enumerate(candidate_images):
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"candidate_{timestamp}_{idx}.png"
            local_path = os.path.join(image_dir, filename)

            try:
                await image_service.download_image(url, local_path)
                local_images.append(local_path)
            except Exception as e:
                print(f"下载图片失败: {e}")
                local_images.append(None)

        # 保存候选图URL（7天有效期）
        await char_repo.update_candidate_images(character_id, candidate_images)
        await db.commit()

        return {
            "message": "人设图生成成功",
            "candidate_images": candidate_images,
            "local_backups": local_images
        }

    except Exception as e:
        # 更新状态为失败
        character.generation_status = GenerationStatus.FAILED
        character.generation_error = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/{character_id}/select-image")
async def select_character_image(
    character_id: int,
    req: CharacterImageSelectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """选择角色人设图"""
    char_repo = CharacterRepository(db)
    character = await char_repo.get_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 验证用户有权限
    script_repo = ScriptRepository(db)
    script = await script_repo.get_by_id(character.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_user_project(script.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="无权访问此角色")

    # 验证候选图存在
    if not character.candidate_images_json:
        raise HTTPException(status_code=400, detail="请先生成候选图")

    if req.image_index < 0 or req.image_index >= len(character.candidate_images_json):
        raise HTTPException(status_code=400, detail="图片索引无效")

    # 选择图片
    selected_image = character.candidate_images_json[req.image_index]
    await char_repo.update_reference_image(character_id, selected_image)

    # TODO: 创建UserAsset记录并关联
    # asset = UserAsset(...)
    # await char_repo.link_to_asset(character_id, asset.id)

    await db.commit()

    return {
        "message": "人设图选择成功",
        "reference_image": selected_image
    }

"""资产管理API端点 - 管理Scene、Item、Costume等资产"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models import Script, Character, Scene, Item, Costume, GenerationTask, GenerationStatus, UserAsset, UserAssetRelation, RelationType
from app.schemas.asset_management import (
    AssetExtractionRequest,
    AssetExtractionResponse,
    SceneResponse,
    ItemResponse,
    CostumeResponse,
    AssetPromptGenerationRequest,
    AssetPromptGenerationResponse,
    ShareAssetsRequest,
    ShareAssetsResponse,
    CreatedAssetInfo,
    CreatedRelationInfo,
    AssetImageSelectRequest,
)
from app.services.asset_extraction_service import AssetExtractionService
from app.services.llm_service import LLMService
from app.services.config_service import get_user_config, ConfigurationError

router = APIRouter(prefix="/asset-management", tags=["资产管理"])


@router.post("/scripts/{script_id}/extract-assets", response_model=AssetExtractionResponse)
async def extract_assets(
    script_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从剧本中提取资产（角色、场景、道具、服装）"""
    # 获取脚本
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 检查用户配置
    try:
        user_config = await get_user_config(db, current_user.id)
    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 创建服务
    llm_service = LLMService(user_config)
    extraction_service = AssetExtractionService(llm_service)

    # 提取资产
    try:
        assets = await extraction_service.extract_assets_from_script(db, script)

        # 保存到数据库
        characters_created = []
        scenes_created = []
        items_created = []
        costumes_created = []

        # 保存角色
        for char_data in assets.get("characters", []):
            char = Character(
                script_id=script_id,
                original_name=char_data["name"],
                gender=char_data.get("gender", "unknown"),
                description=char_data.get("description", ""),
                generation_status=GenerationStatus.PENDING
            )
            db.add(char)
            await db.flush()
            characters_created.append(char)

        # 保存场景
        for scene_data in assets.get("scenes", []):
            scene = Scene(
                script_id=script_id,
                name=scene_data["name"],
                description=scene_data.get("description", ""),
                generation_status=GenerationStatus.PENDING
            )
            db.add(scene)
            await db.flush()
            scenes_created.append(scene)

        # 保存道具
        for item_data in assets.get("items", []):
            item = Item(
                script_id=script_id,
                name=item_data["name"],
                description=item_data.get("description", ""),
                generation_status=GenerationStatus.PENDING
            )
            db.add(item)
            await db.flush()
            items_created.append(item)

        # 保存服装
        skipped_costumes = []
        warnings = []

        for costume_data in assets.get("costumes", []):
            # 尝试关联角色
            character_id = None
            character_name = costume_data.get("character_name")

            if character_name:
                for char in characters_created:
                    if char.original_name == character_name:
                        character_id = char.id
                        break

            if character_id is None:
                # 服装无法匹配到角色，跳过并记录
                skipped_costumes.append(costume_data["name"])
                warning_msg = f"服装 '{costume_data['name']}' 无法匹配到角色"
                if character_name:
                    warning_msg += f" (期望角色: {character_name})"
                warnings.append(warning_msg)
                continue

            costume = Costume(
                script_id=script_id,
                character_id=character_id,
                name=costume_data["name"],
                description=costume_data.get("description", ""),
                generation_status=GenerationStatus.PENDING
            )
            db.add(costume)
            await db.flush()
            costumes_created.append(costume)

        await db.commit()

        return AssetExtractionResponse(
            characters_count=len(characters_created),
            scenes_count=len(scenes_created),
            items_count=len(items_created),
            costumes_count=len(costumes_created),
            skipped_costumes_count=len(skipped_costumes),
            warnings=warnings,
            message="资产提取成功"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"资产提取失败: {str(e)}")


@router.get("/scripts/{script_id}/scenes", response_model=List[SceneResponse])
async def list_scenes(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取脚本的所有场景"""
    result = await db.execute(
        select(Scene).where(Scene.script_id == script_id).order_by(Scene.id)
    )
    scenes = result.scalars().all()

    return [
        SceneResponse(
            id=s.id,
            script_id=s.script_id,
            name=s.name,
            description=s.description,
            image_prompt=s.image_prompt,
            reference_image_path=s.reference_image_path,
            generation_status=s.generation_status.value,
            generation_task_id=s.generation_task_id,
            candidate_images_json=s.candidate_images_json or [],
            user_asset_id=s.user_asset_id,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in scenes
    ]


@router.get("/scripts/{script_id}/items", response_model=List[ItemResponse])
async def list_items(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取脚本的所有道具"""
    result = await db.execute(
        select(Item).where(Item.script_id == script_id).order_by(Item.id)
    )
    items = result.scalars().all()

    return [
        ItemResponse(
            id=i.id,
            script_id=i.script_id,
            name=i.name,
            description=i.description,
            image_prompt=i.image_prompt,
            reference_image_path=i.reference_image_path,
            generation_status=i.generation_status.value,
            generation_task_id=i.generation_task_id,
            candidate_images_json=i.candidate_images_json or [],
            user_asset_id=i.user_asset_id,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in items
    ]


@router.get("/scripts/{script_id}/costumes", response_model=List[CostumeResponse])
async def list_costumes(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取脚本的所有服装"""
    result = await db.execute(
        select(Costume).where(Costume.script_id == script_id).order_by(Costume.id)
    )
    costumes = result.scalars().all()

    # 获取所有角色信息
    character_ids = [c.character_id for c in costumes if c.character_id]
    characters_result = await db.execute(
        select(Character).where(Character.id.in_(character_ids))
    )
    characters = {char.id: char for char in characters_result.scalars().all()}

    return [
        CostumeResponse(
            id=c.id,
            script_id=c.script_id,
            character_id=c.character_id,
            character_name=characters.get(c.character_id).original_name if c.character_id and c.character_id in characters else None,
            name=c.name,
            description=c.description,
            image_prompt=c.image_prompt,
            reference_image_path=c.reference_image_path,
            generation_status=c.generation_status.value,
            generation_task_id=c.generation_task_id,
            candidate_images_json=c.candidate_images_json or [],
            user_asset_id=c.user_asset_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in costumes
    ]


@router.post("/generate-prompt", response_model=AssetPromptGenerationResponse)
async def generate_asset_prompt(
    req: AssetPromptGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为资产生成图像提示词并保存到数据库"""
    # 检查用户配置
    try:
        user_config = await get_user_config(db, current_user.id)
    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 创建服务
    llm_service = LLMService(user_config)
    extraction_service = AssetExtractionService(llm_service)

    try:
        prompt = await extraction_service.generate_asset_prompt(
            asset_type=req.asset_type,
            asset_name=req.asset_name,
            asset_description=req.asset_description,
            additional_context=req.additional_context
        )

        # 保存提示词到对应的资产
        if req.asset_type == 'character':
            result = await db.execute(select(Character).where(Character.id == req.asset_id))
            asset = result.scalar_one_or_none()
            if asset:
                asset.reference_prompt = prompt
        elif req.asset_type == 'scene':
            result = await db.execute(select(Scene).where(Scene.id == req.asset_id))
            asset = result.scalar_one_or_none()
            if asset:
                asset.image_prompt = prompt
        elif req.asset_type == 'item':
            result = await db.execute(select(Item).where(Item.id == req.asset_id))
            asset = result.scalar_one_or_none()
            if asset:
                asset.image_prompt = prompt
        elif req.asset_type == 'costume':
            result = await db.execute(select(Costume).where(Costume.id == req.asset_id))
            asset = result.scalar_one_or_none()
            if asset:
                asset.image_prompt = prompt

        await db.commit()

        return AssetPromptGenerationResponse(
            prompt=prompt,
            asset_type=req.asset_type,
            asset_name=req.asset_name
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"提示词生成失败: {str(e)}")


@router.post("/share", response_model=ShareAssetsResponse)
async def share_assets(
    req: ShareAssetsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量分享资产到资产库
    
    支持混合分享角色、场景、道具、服装
    自动建立服装与角色的从属关系
    """
    try:
        created_assets = []
        created_relations = []
        warnings = []
        
        # 按类型分组
        characters_to_share = [item for item in req.items if item.asset_type == "character"]
        scenes_to_share = [item for item in req.items if item.asset_type == "scene"]
        items_to_share = [item for item in req.items if item.asset_type == "item"]
        costumes_to_share = [item for item in req.items if item.asset_type == "costume"]
        
        # 用于记录源ID到用户资产ID的映射
        character_id_mapping = {}  # {source_character_id: user_asset_id}
        
        # 1. 先分享角色
        for item in characters_to_share:
            result = await db.execute(
                select(Character).where(Character.id == item.source_id)
            )
            character = result.scalar_one_or_none()
            
            if not character:
                warnings.append(f"角色 ID {item.source_id} 不存在")
                continue
            
            # 检查是否已分享
            if character.user_asset_id:
                warnings.append(f"角色 '{character.original_name}' 已分享")
                character_id_mapping[character.id] = character.user_asset_id
                continue
            
            # 创建用户资产
            user_asset = UserAsset(
                user_id=current_user.id,
                asset_type="character",
                original_name=character.original_name,
                description=character.description or "",
                reference_image_path=character.reference_image_path,
                source_project_id=req.project_id,
                source_script_id=req.script_id
            )
            db.add(user_asset)
            await db.flush()
            
            # 更新角色的 user_asset_id
            character.user_asset_id = user_asset.id
            
            character_id_mapping[character.id] = user_asset.id
            created_assets.append(CreatedAssetInfo(
                asset_type="character",
                source_id=character.id,
                user_asset_id=user_asset.id
            ))
        
        # 2. 分享场景
        for item in scenes_to_share:
            result = await db.execute(
                select(Scene).where(Scene.id == item.source_id)
            )
            scene = result.scalar_one_or_none()
            
            if not scene:
                warnings.append(f"场景 ID {item.source_id} 不存在")
                continue
            
            if scene.user_asset_id:
                warnings.append(f"场景 '{scene.name}' 已分享")
                continue
            
            user_asset = UserAsset(
                user_id=current_user.id,
                asset_type="scene",
                original_name=scene.name,
                description=scene.description or "",
                reference_image_path=scene.reference_image_path,
                source_project_id=req.project_id,
                source_script_id=req.script_id
            )
            db.add(user_asset)
            await db.flush()
            
            scene.user_asset_id = user_asset.id
            created_assets.append(CreatedAssetInfo(
                asset_type="scene",
                source_id=scene.id,
                user_asset_id=user_asset.id
            ))
        
        # 3. 分享道具
        for item in items_to_share:
            result = await db.execute(
                select(Item).where(Item.id == item.source_id)
            )
            item_obj = result.scalar_one_or_none()
            
            if not item_obj:
                warnings.append(f"道具 ID {item.source_id} 不存在")
                continue
            
            if item_obj.user_asset_id:
                warnings.append(f"道具 '{item_obj.name}' 已分享")
                continue
            
            user_asset = UserAsset(
                user_id=current_user.id,
                asset_type="item",
                original_name=item_obj.name,
                description=item_obj.description or "",
                reference_image_path=item_obj.reference_image_path,
                source_project_id=req.project_id,
                source_script_id=req.script_id
            )
            db.add(user_asset)
            await db.flush()
            
            item_obj.user_asset_id = user_asset.id
            created_assets.append(CreatedAssetInfo(
                asset_type="item",
                source_id=item_obj.id,
                user_asset_id=user_asset.id
            ))
        
        # 4. 分享服装并建立关系
        for item in costumes_to_share:
            result = await db.execute(
                select(Costume).where(Costume.id == item.source_id)
            )
            costume = result.scalar_one_or_none()
            
            if not costume:
                warnings.append(f"服装 ID {item.source_id} 不存在")
                continue
            
            if costume.user_asset_id:
                warnings.append(f"服装 '{costume.name}' 已分享")
                continue
            
            # 创建服装资产
            user_asset = UserAsset(
                user_id=current_user.id,
                asset_type="costume",
                original_name=costume.name,
                description=costume.description or "",
                reference_image_path=costume.reference_image_path,
                source_project_id=req.project_id,
                source_script_id=req.script_id
            )
            db.add(user_asset)
            await db.flush()
            
            costume.user_asset_id = user_asset.id
            created_assets.append(CreatedAssetInfo(
                asset_type="costume",
                source_id=costume.id,
                user_asset_id=user_asset.id
            ))
            
            # 尝试建立与角色的关系
            character_asset_id = None
            
            # 先查看本次分享中是否包含对应角色
            if costume.character_id in character_id_mapping:
                character_asset_id = character_id_mapping[costume.character_id]
            else:
                # 查看角色是否已经分享过
                result = await db.execute(
                    select(Character).where(Character.id == costume.character_id)
                )
                character = result.scalar_one_or_none()
                if character and character.user_asset_id:
                    character_asset_id = character.user_asset_id
            
            # 如果找到了角色资产，建立关系
            if character_asset_id:
                # 检查关系是否已存在
                existing_relation = await db.execute(
                    select(UserAssetRelation).where(
                        UserAssetRelation.user_id == current_user.id,
                        UserAssetRelation.from_asset_id == user_asset.id,
                        UserAssetRelation.to_asset_id == character_asset_id,
                        UserAssetRelation.relation_type == RelationType.BELONGS_TO_CHARACTER
                    )
                )
                if not existing_relation.scalar_one_or_none():
                    relation = UserAssetRelation(
                        user_id=current_user.id,
                        from_asset_id=user_asset.id,
                        to_asset_id=character_asset_id,
                        relation_type=RelationType.BELONGS_TO_CHARACTER,
                        source_project_id=req.project_id,
                        source_script_id=req.script_id
                    )
                    db.add(relation)
                    await db.flush()
                    
                    created_relations.append(CreatedRelationInfo(
                        relation_type="belongs_to_character",
                        from_asset_id=user_asset.id,
                        to_asset_id=character_asset_id
                    ))
        
        await db.commit()
        
        return ShareAssetsResponse(
            created_assets=created_assets,
            created_relations=created_relations,
            warnings=warnings,
            message=f"成功分享 {len(created_assets)} 个资产，建立 {len(created_relations)} 个关系"
        )
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"分享失败: {str(e)}")


@router.post("/scenes/{scene_id}/select-image")
async def select_scene_image(
    scene_id: int,
    req: AssetImageSelectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """选择场景参考图"""
    # 获取场景
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 验证用户有权限
    script_result = await db.execute(select(Script).where(Script.id == scene.script_id))
    script = script_result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 验证候选图存在
    if not scene.candidate_images_json:
        raise HTTPException(status_code=400, detail="请先生成候选图")

    if req.image_index < 0 or req.image_index >= len(scene.candidate_images_json):
        raise HTTPException(status_code=400, detail="图片索引无效")

    # 选择图片
    selected_image = scene.candidate_images_json[req.image_index]
    scene.has_reference_image = 1
    scene.reference_image_path = selected_image.get("url") if isinstance(selected_image, dict) else selected_image
    await db.commit()

    return {
        "message": "场景参考图选择成功",
        "reference_image": scene.reference_image_path
    }


@router.post("/items/{item_id}/select-image")
async def select_item_image(
    item_id: int,
    req: AssetImageSelectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """选择道具参考图"""
    # 获取道具
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="道具不存在")

    # 验证用户有权限
    script_result = await db.execute(select(Script).where(Script.id == item.script_id))
    script = script_result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 验证候选图存在
    if not item.candidate_images_json:
        raise HTTPException(status_code=400, detail="请先生成候选图")

    if req.image_index < 0 or req.image_index >= len(item.candidate_images_json):
        raise HTTPException(status_code=400, detail="图片索引无效")

    # 选择图片
    selected_image = item.candidate_images_json[req.image_index]
    item.has_reference_image = 1
    item.reference_image_path = selected_image.get("url") if isinstance(selected_image, dict) else selected_image
    await db.commit()

    return {
        "message": "道具参考图选择成功",
        "reference_image": item.reference_image_path
    }


@router.post("/costumes/{costume_id}/select-image")
async def select_costume_image(
    costume_id: int,
    req: AssetImageSelectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """选择服装参考图"""
    # 获取服装
    result = await db.execute(select(Costume).where(Costume.id == costume_id))
    costume = result.scalar_one_or_none()
    if not costume:
        raise HTTPException(status_code=404, detail="服装不存在")

    # 验证用户有权限
    script_result = await db.execute(select(Script).where(Script.id == costume.script_id))
    script = script_result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    # 验证候选图存在
    if not costume.candidate_images_json:
        raise HTTPException(status_code=400, detail="请先生成候选图")

    if req.image_index < 0 or req.image_index >= len(costume.candidate_images_json):
        raise HTTPException(status_code=400, detail="图片索引无效")

    # 选择图片
    selected_image = costume.candidate_images_json[req.image_index]
    costume.has_reference_image = 1
    costume.reference_image_path = selected_image.get("url") if isinstance(selected_image, dict) else selected_image
    await db.commit()

    return {
        "message": "服装参考图选择成功",
        "reference_image": costume.reference_image_path
    }

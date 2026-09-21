import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.asset import AssetType
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.asset import (
    AssetCreate,
    AssetResponse,
    CharacterGenerationRequest,
    CharacterGenerationResponse,
    CharacterConfirmRequest,
)
from app.services.character_service import CharacterService
from app.services.llm_service import LLMService
from app.services.seedream_service import SeedreamService
from app.services.config_service import get_user_config, ConfigurationError

router = APIRouter(prefix="/assets", tags=["资产库"])


@router.get("", response_model=List[AssetResponse])
async def list_assets(
    asset_type: Optional[str] = Query(None, alias="type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = AssetRepository(db)
    type_enum = AssetType(asset_type) if asset_type else None
    if type_enum and asset_type not in [t.value for t in AssetType]:
        raise HTTPException(status_code=400, detail=f"无效的资产类型: {asset_type}")

    assets = await repo.list_by_user(current_user.id, type_enum)
    return [
        AssetResponse(
            id=a.id,
            asset_type=a.asset_type.value,
            original_name=a.original_name,
            alias_name=a.alias_name,
            gender=a.gender,
            prompt_description=a.prompt_description,
            image_url=a.image_url,
            image_path=a.image_path,
            created_at=a.created_at,
        )
        for a in assets
    ]


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = AssetRepository(db)
    asset = await repo.get_by_id(asset_id)
    if not asset or asset.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="资产不存在")

    return AssetResponse(
        id=asset.id,
        asset_type=asset.asset_type.value,
        original_name=asset.original_name,
        alias_name=asset.alias_name,
        gender=asset.gender,
        prompt_description=asset.prompt_description,
        image_url=asset.image_url,
        image_path=asset.image_path,
        created_at=asset.created_at,
    )


@router.post("", response_model=AssetResponse, status_code=201)
async def create_asset(
    req: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.asset_type not in [t.value for t in AssetType]:
        raise HTTPException(status_code=400, detail=f"无效的资产类型: {req.asset_type}")

    repo = AssetRepository(db)
    asset = await repo.create(
        user_id=current_user.id,
        asset_type=AssetType(req.asset_type),
        original_name=req.original_name,
        alias_name=f"[{req.asset_type}_{uuid.uuid4().hex[:8]}]",
        prompt_description=req.prompt_description,
        image_url=req.image_url,
        gender=req.gender,
    )

    return AssetResponse(
        id=asset.id,
        asset_type=asset.asset_type.value,
        original_name=asset.original_name,
        alias_name=asset.alias_name,
        prompt_description=asset.prompt_description,
        image_url=asset.image_url,
    )


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = AssetRepository(db)
    asset = await repo.get_by_id(asset_id)
    if not asset or asset.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="资产不存在")

    await repo.delete(asset_id)


@router.post("/generate-character", response_model=CharacterGenerationResponse)
async def generate_character(
    req: CharacterGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user_config = await get_user_config(db, current_user.id)
    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    llm = LLMService(user_config)
    seedream = SeedreamService(user_config)
    char_service = CharacterService(llm, seedream)

    characters = {"target": {
        "alias": "角色",
        "gender": "unknown",
        "description": req.description,
    }}
    result = await char_service.generate_character_images(characters, count=req.count)

    images = result.get("target", {}).get("candidate_images", [])
    task_id = uuid.uuid4().hex[:12]

    return CharacterGenerationResponse(images=images, task_id=task_id)


@router.post("/confirm-character", response_model=AssetResponse)
async def confirm_character(
    req: CharacterConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = AssetRepository(db)
    alias = req.alias_name or f"[角色_{uuid.uuid4().hex[:8]}]"

    asset = await repo.create(
        user_id=current_user.id,
        asset_type=AssetType.CHARACTER,
        original_name=req.original_name,
        alias_name=alias,
        prompt_description=req.prompt_description,
        image_url=req.image_url,
        gender=req.gender,
        source_project_id=req.project_id,
    )

    return AssetResponse(
        id=asset.id,
        asset_type=asset.asset_type.value,
        original_name=asset.original_name,
        alias_name=asset.alias_name,
        gender=asset.gender,
        prompt_description=asset.prompt_description,
        image_url=asset.image_url,
        created_at=asset.created_at,
    )

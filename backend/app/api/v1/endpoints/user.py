from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import ChangePasswordRequest
from app.schemas.user_settings import UserSettingsUpdate, UserSettingsPublic
from app.repositories.user_settings_repository import UserSettingsRepository
from app.repositories.user_repository import UserRepository
from app.services.config_service import get_effective_config_values
from app.services.email_service import EmailService

router = APIRouter(prefix="/user", tags=["用户"])
email_service = EmailService()


@router.get("/settings", response_model=UserSettingsPublic)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的API配置"""
    settings = await UserSettingsRepository.get_by_user_id(db, current_user.id)
    effective = get_effective_config_values(settings)

    return UserSettingsPublic(
        id=settings.id if settings else 0,
        user_id=current_user.id,
        llm_api_type=effective["llm_api_type"],
        llm_base_url=effective["llm_base_url"],
        llm_api_key_configured=bool(effective["llm_api_key"]),
        llm_model_main=effective["llm_model_main"],
        llm_model_fast=effective["llm_model_fast"],
        seedream_api_type=effective["seedream_api_type"],
        seedream_base_url=effective["seedream_base_url"],
        seedream_api_key_configured=bool(effective["seedream_api_key"]),
        seedream_model=effective["seedream_model"],
        seedance_api_type=effective["seedance_api_type"],
        seedance_base_url=effective["seedance_base_url"],
        seedance_api_key_configured=bool(effective["seedance_api_key"]),
        seedance_model=effective["seedance_model"],
    )


@router.put("/settings", response_model=UserSettingsPublic)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户的API配置"""
    settings = await UserSettingsRepository.get_or_create(db, current_user.id)

    # 只更新非None的字段
    update_data = settings_update.model_dump(exclude_unset=True)
    for key_field in ("llm_api_key", "seedream_api_key", "seedance_api_key"):
        if update_data.get(key_field) is None:
            update_data.pop(key_field, None)
    settings = await UserSettingsRepository.update(db, settings, **update_data)
    effective = get_effective_config_values(settings)

    return UserSettingsPublic(
        id=settings.id,
        user_id=settings.user_id,
        llm_api_type=effective["llm_api_type"],
        llm_base_url=effective["llm_base_url"],
        llm_api_key_configured=bool(effective["llm_api_key"]),
        llm_model_main=effective["llm_model_main"],
        llm_model_fast=effective["llm_model_fast"],
        seedream_api_type=effective["seedream_api_type"],
        seedream_base_url=effective["seedream_base_url"],
        seedream_api_key_configured=bool(effective["seedream_api_key"]),
        seedream_model=effective["seedream_model"],
        seedance_api_type=effective["seedance_api_type"],
        seedance_base_url=effective["seedance_base_url"],
        seedance_api_key_configured=bool(effective["seedance_api_key"]),
        seedance_model=effective["seedance_model"],
    )


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码

    两种方式：
    1. 提供旧密码 + 新密码
    2. 提供邮箱验证码 + 新密码（用于忘记密码或首次设置密码）
    """
    user_repo = UserRepository(db)

    # 方式1：使用旧密码验证
    if req.old_password:
        if not verify_password(req.old_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
    # 方式2：使用邮箱验证码
    elif req.verification_code:
        if not email_service.verify_code(current_user.email, req.verification_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码无效或已过期"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供旧密码或邮箱验证码"
        )

    # 更新密码
    new_password_hash = hash_password(req.new_password)
    await user_repo.update_password(current_user.id, new_password_hash)
    await db.commit()

    return {"message": "密码修改成功"}

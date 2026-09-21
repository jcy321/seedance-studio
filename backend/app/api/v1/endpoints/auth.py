from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.auth import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["认证"])
email_service = EmailService()


@router.post("/send-code", response_model=EmailVerificationResponse)
async def send_verification_code(req: EmailVerificationRequest):
    try:
        code = await email_service.send_verification_code(req.email)
        return EmailVerificationResponse(
            message=f"验证码已发送至 {req.email}",
            expires_in=600,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)

    # 验证验证码
    if not email_service.verify_code(req.email, req.verification_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码无效或已过期",
        )

    # 检查邮箱是否已注册
    existing = await repo.get_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已注册",
        )

    # 创建用户
    user = await repo.create_user(
        email=req.email,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
    )

    # 生成JWT
    token = create_access_token({"user_id": user.id, "email": user.email})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        nickname=user.nickname,
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(req.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    token = create_access_token({"user_id": user.id, "email": user.email})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        nickname=user.nickname,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

from pydantic import BaseModel, Field
from typing import Optional


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=100)


class ChangePasswordRequest(BaseModel):
    old_password: Optional[str] = Field(None, description="旧密码（如果之前没有设置密码则不需要）")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    verification_code: Optional[str] = Field(None, description="邮箱验证码（如果没有旧密码则需要）")

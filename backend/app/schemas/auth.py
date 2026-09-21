from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationResponse(BaseModel):
    message: str
    expires_in: int = 600


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    verification_code: str = Field(..., min_length=6, max_length=6)
    nickname: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    nickname: Optional[str] = None

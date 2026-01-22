from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    onboarding_completed: bool = False
    last_login_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


class TokenData(BaseModel):
    user: UserResponse
    token: str
    refresh_token: str

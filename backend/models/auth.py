from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


def validate_password_strength(password: str) -> str:
    """Validate password meets minimum security requirements."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise ValueError("Password must be less than 128 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one number")
    return password


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return validate_password_strength(v)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v):
        # Strip HTML tags
        return re.sub(r"<[^>]+>", "", v).strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, max_length=2048)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=2048)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return validate_password_strength(v)


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=10)


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

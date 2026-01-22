from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
from models.auth import (
    SignupRequest,
    LoginRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyCodeRequest,
    AuthResponse,
    UserResponse,
)
from core.supabase import get_supabase, get_supabase_admin
from core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
)
from supabase_auth.errors import AuthApiError

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """Register a new user account."""
    supabase = get_supabase()

    try:
        # Sign up with Supabase Auth
        auth_response = supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
                "options": {"data": {"name": request.name}},
            }
        )

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user",
            )

        user_id = auth_response.user.id

        # Create tokens
        token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})

        user_data = UserResponse(
            id=user_id,
            email=request.email,
            name=request.name,
            onboarding_completed=False,
        )

        return AuthResponse(
            success=True,
            data={
                "user": user_data.model_dump(),
                "token": token,
                "refresh_token": refresh_token,
            },
        )

    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Authenticate user and return tokens."""
    supabase = get_supabase()

    try:
        # Sign in with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password}
        )

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        user_id = auth_response.user.id

        # Get user profile from database
        user_profile = (
            supabase.table("users").select("*").eq("id", user_id).single().execute()
        )

        # Update last login time
        supabase.table("users").update(
            {"last_login_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", user_id).execute()

        # Create tokens
        token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})

        user_data = user_profile.data if user_profile.data else {}

        return AuthResponse(
            success=True,
            data={
                "user": {
                    "id": user_id,
                    "email": request.email,
                    "name": user_data.get("name"),
                    "onboarding_completed": user_data.get("onboarding_completed", False),
                    "last_login_at": datetime.now(timezone.utc).isoformat(),
                },
                "token": token,
                "refresh_token": refresh_token,
            },
        )

    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@router.post("/logout", response_model=AuthResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Log out the current user."""
    supabase = get_supabase()

    try:
        supabase.auth.sign_out()
        return AuthResponse(success=True, message="Successfully logged out")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )


@router.post("/refresh-token", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh the access token using a refresh token."""
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Create new tokens
        new_access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})

        return AuthResponse(
            success=True,
            data={
                "token": new_access_token,
                "refresh_token": new_refresh_token,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/verify-code", response_model=AuthResponse)
async def verify_code(request: VerifyCodeRequest):
    """Verify email with OTP code."""
    supabase = get_supabase()

    try:
        auth_response = supabase.auth.verify_otp(
            {"email": request.email, "token": request.code, "type": "email"}
        )

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        return AuthResponse(success=True, message="Email verified successfully")

    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email."""
    supabase = get_supabase()

    try:
        supabase.auth.reset_password_email(request.email)
        return AuthResponse(success=True, message="Password reset email sent")

    except AuthApiError as e:
        # Don't reveal if email exists
        return AuthResponse(success=True, message="Password reset email sent")


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(request: ResetPasswordRequest):
    """Reset password with token from email."""
    supabase = get_supabase()

    try:
        # Verify the reset token and update password
        auth_response = supabase.auth.verify_otp(
            {"token_hash": request.token, "type": "recovery"}
        )

        if auth_response.user:
            supabase.auth.update_user({"password": request.password})
            return AuthResponse(success=True, message="Password reset successful")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

from fastapi import APIRouter, HTTPException, status, Depends, Request
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
from core.supabase import get_supabase
from core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    blacklist_token,
)
from core.rate_limit import check_rate_limit
from supabase_auth.errors import AuthApiError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request_data: SignupRequest, request: Request):
    """Register a new user account."""
    check_rate_limit(request, max_requests=3, window_seconds=60)

    supabase = get_supabase()

    try:
        # Sign up with Supabase Auth
        auth_response = supabase.auth.sign_up(
            {
                "email": request_data.email,
                "password": request_data.password,
                "options": {"data": {"name": request_data.name}},
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
            email=request_data.email,
            name=request_data.name,
            onboarding_completed=False,
        )

        logger.info(f"AUTH_AUDIT: signup success email={request_data.email}")

        return AuthResponse(
            success=True,
            data={
                "user": user_data.model_dump(),
                "token": token,
                "refresh_token": refresh_token,
            },
        )

    except HTTPException:
        raise
    except AuthApiError as e:
        logger.warning(f"AUTH_AUDIT: signup failed email={request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=AuthResponse)
async def login(request_data: LoginRequest, request: Request):
    """Authenticate user and return tokens."""
    check_rate_limit(request, max_requests=5, window_seconds=60)

    supabase = get_supabase()

    try:
        # Sign in with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password(
            {"email": request_data.email, "password": request_data.password}
        )

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        user_id = auth_response.user.id

        # Get user profile from database
        user_profile = (
            supabase.table("users").select("*").eq("id", user_id).execute()
        )

        # Update last login time
        supabase.table("users").update(
            {"last_login_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", user_id).execute()

        # Create tokens
        token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})

        user_data = user_profile.data[0] if user_profile.data else {}

        logger.info(f"AUTH_AUDIT: login success user_id={user_id}")

        return AuthResponse(
            success=True,
            data={
                "user": {
                    "id": user_id,
                    "email": request_data.email,
                    "name": user_data.get("name"),
                    "onboarding_completed": user_data.get("onboarding_completed", False),
                    "last_login_at": datetime.now(timezone.utc).isoformat(),
                },
                "token": token,
                "refresh_token": refresh_token,
            },
        )

    except HTTPException:
        raise
    except AuthApiError:
        logger.warning(f"AUTH_AUDIT: login failed email={request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@router.post("/logout", response_model=AuthResponse)
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Log out the current user and invalidate tokens."""
    supabase = get_supabase()

    try:
        # Blacklist the current access token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            blacklist_token(token)

        supabase.auth.sign_out()
        logger.info(f"AUTH_AUDIT: logout user_id={current_user['id']}")
        return AuthResponse(success=True, message="Successfully logged out")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )


@router.post("/refresh-token", response_model=AuthResponse)
async def refresh_token(request_data: RefreshTokenRequest, request: Request):
    """Refresh the access token using a refresh token."""
    check_rate_limit(request, max_requests=10, window_seconds=60)

    try:
        payload = verify_token(request_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Blacklist the old refresh token (token rotation)
        blacklist_token(request_data.refresh_token)

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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/verify-code", response_model=AuthResponse)
async def verify_code(request_data: VerifyCodeRequest, request: Request):
    """Verify email with OTP code."""
    check_rate_limit(request, max_requests=5, window_seconds=60)

    supabase = get_supabase()

    try:
        auth_response = supabase.auth.verify_otp(
            {"email": request_data.email, "token": request_data.code, "type": "email"}
        )

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        return AuthResponse(success=True, message="Email verified successfully")

    except HTTPException:
        raise
    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )


@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(request_data: ForgotPasswordRequest, request: Request):
    """Send password reset email."""
    check_rate_limit(request, max_requests=3, window_seconds=60)

    supabase = get_supabase()

    try:
        supabase.auth.reset_password_email(request_data.email)
    except AuthApiError:
        pass  # Don't reveal if email exists

    # Always return success to prevent email enumeration
    return AuthResponse(success=True, message="If that email exists, a reset link has been sent")


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(request_data: ResetPasswordRequest, request: Request):
    """Reset password with token from email."""
    check_rate_limit(request, max_requests=3, window_seconds=60)

    supabase = get_supabase()

    try:
        # Verify the reset token and update password
        auth_response = supabase.auth.verify_otp(
            {"token_hash": request_data.token, "type": "recovery"}
        )

        if auth_response.user:
            supabase.auth.update_user({"password": request_data.password})
            logger.info(f"AUTH_AUDIT: password reset user_id={auth_response.user.id}")
            return AuthResponse(success=True, message="Password reset successful")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    except HTTPException:
        raise
    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

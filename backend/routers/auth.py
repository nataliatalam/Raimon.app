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
    GoogleAuthRequest,
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

        # Create tokens (include email for auto-profile creation)
        token = create_access_token(data={"sub": user_id, "email": request_data.email})
        refresh_token = create_refresh_token(data={"sub": user_id, "email": request_data.email})

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

        # Create tokens (include email for auto-profile creation)
        token = create_access_token(data={"sub": user_id, "email": request_data.email})
        refresh_token = create_refresh_token(data={"sub": user_id, "email": request_data.email})

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
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Blacklist the old refresh token (token rotation)
        blacklist_token(request_data.refresh_token)

        # Create new tokens (preserve email for auto-profile creation)
        new_access_token = create_access_token(data={"sub": user_id, "email": email})
        new_refresh_token = create_refresh_token(data={"sub": user_id, "email": email})

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


@router.post("/google", response_model=AuthResponse)
async def google_auth(request_data: GoogleAuthRequest, request: Request):
    """Exchange Supabase OAuth token for backend JWT tokens with account linking."""
    check_rate_limit(request, max_requests=10, window_seconds=60)

    supabase = get_supabase()

    try:
        # Verify the Supabase access token and get user
        user_response = supabase.auth.get_user(request_data.access_token)

        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
            )

        user = user_response.user
        google_user_id = user.id
        email = user.email
        name = user.user_metadata.get("full_name") or user.user_metadata.get("name") or ""

        # First, check if user exists by email (for account linking)
        existing_by_email = (
            supabase.table("users").select("*").eq("email", email).execute()
        )

        if existing_by_email.data:
            # Account linking: user exists with same email (e.g., signed up with password before)
            existing_user = existing_by_email.data[0]
            user_id = existing_user.get("id")
            onboarding_completed = existing_user.get("onboarding_completed", False)
            name = existing_user.get("name") or name

            # Update last login
            supabase.table("users").update(
                {"last_login_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", user_id).execute()

            logger.info(f"AUTH_AUDIT: google auth linked to existing account user_id={user_id}")
        else:
            # Check if user exists by Google user ID
            user_profile = (
                supabase.table("users").select("*").eq("id", google_user_id).execute()
            )

            if user_profile.data:
                # User exists with this Google ID
                user_id = google_user_id
                onboarding_completed = user_profile.data[0].get("onboarding_completed", False)
                name = user_profile.data[0].get("name") or name

                # Update last login
                supabase.table("users").update(
                    {"last_login_at": datetime.now(timezone.utc).isoformat()}
                ).eq("id", user_id).execute()
            else:
                # New user - create profile
                user_id = google_user_id
                supabase.table("users").insert({
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "onboarding_completed": False,
                }).execute()
                onboarding_completed = False

                logger.info(f"AUTH_AUDIT: google auth new user created user_id={user_id}")

        # Create backend JWT tokens
        token = create_access_token(data={"sub": user_id, "email": email})
        refresh_token = create_refresh_token(data={"sub": user_id, "email": email})

        logger.info(f"AUTH_AUDIT: google auth success user_id={user_id}")

        return AuthResponse(
            success=True,
            data={
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "onboarding_completed": onboarding_completed,
                },
                "token": token,
                "refresh_token": refresh_token,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"AUTH_AUDIT: google auth failed error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed",
        )

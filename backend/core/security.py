from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import get_settings
from core.supabase import get_supabase
import threading
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()

# In-memory token blacklist (use Redis in production)
_token_blacklist: Set[str] = set()
_blacklist_lock = threading.Lock()

# Columns to select for user profile (avoid exposing internal fields)
USER_SAFE_COLUMNS = "id, email, name, avatar_url, onboarding_completed, onboarding_step, created_at, updated_at"


def blacklist_token(token: str):
    """Add a token to the blacklist."""
    with _blacklist_lock:
        _token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    with _blacklist_lock:
        return token in _token_blacklist


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.refresh_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict:
    # Check blacklist
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # Use appropriate key based on token type
    secret_key = settings.jwt_secret_key if token_type == "access" else settings.refresh_secret_key

    try:
        payload = jwt.decode(
            token, secret_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    try:
        supabase = get_supabase()
        response = (
            supabase.table("users")
            .select(USER_SAFE_COLUMNS)
            .eq("id", user_id)
            .execute()
        )

        if not response.data:
            # Auto-create user profile if it doesn't exist
            email = payload.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token - missing email",
                )

            # Create user profile
            new_user = {
                "id": user_id,
                "email": email,
                "name": payload.get("name") or email.split("@")[0],
                "onboarding_completed": False,
                "onboarding_step": 0,
            }
            create_response = supabase.table("users").insert(new_user).execute()

            if not create_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user profile",
                )

            logger.info(f"Auto-created user profile for {email}")
            return create_response.data[0]

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate user",
        )

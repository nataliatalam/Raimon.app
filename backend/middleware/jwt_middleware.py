"""
JWT authentication middleware for Raimon API.

Validates JWT tokens in requests and extracts user information.
"""
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any
import jwt
import logging
import os

logger = logging.getLogger(__name__)

security = HTTPBearer()


class JWTMiddleware:
    """
    JWT token validation middleware.

    Validates JWT tokens in Authorization headers and extracts user claims.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        verify_exp: bool = True,
    ):
        """
        Initialize JWT middleware.

        Args:
            secret_key: JWT secret key (from env if None)
            algorithm: JWT algorithm (default HS256)
            verify_exp: Whether to verify token expiration
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "your-secret-key")
        self.algorithm = algorithm
        self.verify_exp = verify_exp

        if self.secret_key == "your-secret-key":
            logger.warning("Using default JWT secret key - set JWT_SECRET_KEY in environment")

    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Middleware call - validate JWT in request.

        Args:
            request: FastAPI request object

        Returns:
            Decoded JWT payload or None if no token

        Raises:
            HTTPException: If token is invalid or expired
        """
        # Skip validation for public endpoints
        if self._is_public_endpoint(request.url.path):
            return None

        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Extract token from "Bearer <token>"
            scheme, token = auth_header.split(" ")
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate and decode token
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": self.verify_exp},
            )

            # Store decoded payload in request for use in endpoints
            request.state.user = payload

            logger.debug(f"JWT validated for user: {payload.get('sub', 'unknown')}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def _is_public_endpoint(path: str) -> bool:
        """
        Check if endpoint is public (no auth required).

        Args:
            path: Request path

        Returns:
            True if endpoint is public
        """
        public_paths = [
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
        ]

        return any(path.startswith(p) for p in public_paths)

    @staticmethod
    def create_token(
        data: Dict[str, Any],
        secret_key: str,
        algorithm: str = "HS256",
        expires_delta: Optional[int] = None,
    ) -> str:
        """
        Create a JWT token.

        Args:
            data: Claims to encode
            secret_key: Secret key for signing
            algorithm: Algorithm to use
            expires_delta: Expiration time in seconds

        Returns:
            Encoded JWT token
        """
        from datetime import datetime, timedelta

        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=24)

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        return encoded_jwt


def setup_jwt_middleware(app) -> None:
    """
    Setup JWT middleware for FastAPI app.

    Args:
        app: FastAPI application instance
    """
    jwt_middleware = JWTMiddleware()

    @app.middleware("http")
    async def jwt_auth_middleware(request: Request, call_next):
        """FastAPI middleware wrapper."""
        try:
            await jwt_middleware(request)
        except HTTPException:
            raise

        response = await call_next(request)
        return response

    logger.info("JWT middleware configured")


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current user from request state.

    Used in endpoint dependencies.

    Args:
        request: FastAPI request

    Returns:
        User payload from JWT

    Raises:
        HTTPException: If no user in request state
    """
    user = getattr(request.state, "user", None)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user

"""
Middleware components for Raimon.

Contains FastAPI middleware for CORS, JWT, request limits, rate limiting, etc.
"""

from middleware.cors_middleware import (
    setup_cors_middleware,
    get_cors_origins,
    get_cors_config,
)
from middleware.jwt_middleware import (
    JWTMiddleware,
    setup_jwt_middleware,
    get_current_user,
)
from middleware.request_size_limit import (
    RequestSizeLimitMiddleware,
    RateLimitMiddleware,
    setup_request_size_limit,
    setup_rate_limit_middleware,
)

__all__ = [
    # CORS
    "setup_cors_middleware",
    "get_cors_origins",
    "get_cors_config",
    # JWT
    "JWTMiddleware",
    "setup_jwt_middleware",
    "get_current_user",
    # Request size and rate limiting
    "RequestSizeLimitMiddleware",
    "RateLimitMiddleware",
    "setup_request_size_limit",
    "setup_rate_limit_middleware",
]

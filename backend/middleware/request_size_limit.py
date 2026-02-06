"""
Request size limiting middleware for Raimon API.

Prevents abuse by limiting request body size and prevents DDoS attacks.
"""

from fastapi import Request, HTTPException, status
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class RequestSizeLimitMiddleware:
    """
    Middleware to limit request body size.

    Helps prevent abuse and resource exhaustion from oversized requests.
    """

    def __init__(self, max_content_length_mb: int = 10):
        """
        Initialize request size limit middleware.

        Args:
            max_content_length_mb: Maximum content length in MB (default 10)
        """
        self.max_content_length = max_content_length_mb * 1024 * 1024  # Convert to bytes
        logger.info(f"Request size limit set to {max_content_length_mb} MB")

    async def __call__(self, request: Request, call_next: Callable):
        """
        Middleware call - check request size.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler

        Returns:
            Response from next handler or error response

        Raises:
            HTTPException: If request exceeds size limit
        """
        # Get content length from header
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                content_length = int(content_length)

                if content_length > self.max_content_length:
                    logger.warning(
                        f"Request rejected: size {content_length} bytes exceeds "
                        f"limit {self.max_content_length} bytes"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request body too large. "
                               f"Maximum: {self.max_content_length / 1024 / 1024:.0f} MB",
                    )
            except ValueError:
                logger.warning("Invalid content-length header")

        response = await call_next(request)
        return response


def setup_request_size_limit(
    app,
    max_content_length_mb: int = 10
) -> None:
    """
    Setup request size limit middleware for FastAPI app.

    Args:
        app: FastAPI application instance
        max_content_length_mb: Maximum content length in MB
    """
    middleware = RequestSizeLimitMiddleware(max_content_length_mb=max_content_length_mb)

    @app.middleware("http")
    async def request_size_middleware(request: Request, call_next: Callable):
        """FastAPI middleware wrapper."""
        return await middleware(request, call_next)

    logger.info(f"Request size limit middleware configured ({max_content_length_mb} MB max)")


class RateLimitMiddleware:
    """
    Simple rate limiting middleware (per-IP).

    Tracks requests per IP and enforces rate limit.
    """

    def __init__(self, requests_per_minute: int = 100):
        """
        Initialize rate limit middleware.

        Args:
            requests_per_minute: Maximum requests per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # IP -> [(timestamp, count), ...]

    async def __call__(self, request: Request, call_next: Callable):
        """
        Middleware call - check rate limit.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler

        Returns:
            Response from next handler or rate limit error
        """
        from datetime import datetime, timedelta

        client_ip = self._get_client_ip(request)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)

        # Initialize if first request from this IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []

        # Remove old requests outside the 1-minute window
        self.request_counts[client_ip] = [
            ts for ts in self.request_counts[client_ip]
            if ts > cutoff
        ]

        # Check if limit exceeded
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": "60"},
            )

        # Record this request
        self.request_counts[client_ip].append(now)

        response = await call_next(request)

        # Add rate limit info to response headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.request_counts[client_ip])
        )

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """
        Get client IP from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for proxy headers first (X-Forwarded-For)
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # X-Forwarded-For can be comma-separated, take first
            return x_forwarded_for.split(",")[0].strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"


def setup_rate_limit_middleware(
    app,
    requests_per_minute: int = 100
) -> None:
    """
    Setup rate limit middleware for FastAPI app.

    Args:
        app: FastAPI application instance
        requests_per_minute: Maximum requests per minute per IP
    """
    middleware = RateLimitMiddleware(requests_per_minute=requests_per_minute)

    @app.middleware("http")
    async def rate_limit_request_middleware(request: Request, call_next: Callable):
        """FastAPI middleware wrapper."""
        return await middleware(request, call_next)

    logger.info(f"Rate limit middleware configured ({requests_per_minute} req/min)")

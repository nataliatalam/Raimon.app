from fastapi import HTTPException, Request, status
from datetime import datetime, timezone
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)

# In-memory rate limit store (use Redis in production)
_rate_store: dict = defaultdict(list)
_store_lock = threading.Lock()


def _cleanup_old_entries(key: str, window_seconds: int):
    """Remove entries older than the window."""
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - window_seconds
    _rate_store[key] = [ts for ts in _rate_store[key] if ts > cutoff]


def check_rate_limit(request: Request, max_requests: int, window_seconds: int = 60):
    """
    Check if the request is within rate limits.
    Raises HTTPException 429 if rate limit is exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path
    key = f"{client_ip}:{endpoint}"

    with _store_lock:
        _cleanup_old_entries(key, window_seconds)

        if len(_rate_store[key]) >= max_requests:
            logger.warning(
                f"RATE_LIMIT: {client_ip} exceeded {max_requests}/{window_seconds}s on {endpoint}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

        _rate_store[key].append(datetime.now(timezone.utc).timestamp())

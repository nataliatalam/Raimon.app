"""
CORS middleware for Raimon API.

Configures Cross-Origin Resource Sharing (CORS) policies for the application.
"""

from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import logging

logger = logging.getLogger(__name__)


def get_cors_origins() -> List[str]:
    """
    Get list of allowed CORS origins from environment or defaults.

    Returns:
        List of allowed origin URLs
    """
    # Get from environment variable, or use defaults
    origins_env = os.getenv("CORS_ORIGINS", "")

    if origins_env:
        # Parse comma-separated origins
        origins = [o.strip() for o in origins_env.split(",")]
    else:
        # Default origins for development and production
        origins = [
            "http://localhost:3000",  # Local development
            "http://localhost:8000",  # Local API
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]

    # Add production domains if specified
    production_domain = os.getenv("PRODUCTION_DOMAIN", "")
    if production_domain:
        origins.append(f"https://{production_domain}")
        origins.append(f"http://{production_domain}")

    logger.info(f"CORS origins configured: {origins}")
    return origins


def setup_cors_middleware(app) -> None:
    """
    Setup CORS middleware for FastAPI app.

    Args:
        app: FastAPI application instance
    """
    origins = get_cors_origins()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["Content-Length", "X-Request-ID"],
        max_age=3600,  # Cache preflight for 1 hour
    )

    logger.info("CORS middleware configured")


def get_cors_config() -> dict:
    """
    Get CORS configuration dictionary.

    Useful for documenting or testing CORS settings.

    Returns:
        Dictionary with CORS configuration
    """
    return {
        "allow_origins": get_cors_origins(),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["*"],
        "max_age": 3600,
    }

"""
FastAPI middleware for automatic request tracking with Opik
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
from .client import get_opik_client


class OpikMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track all API requests with Opik

    This middleware captures:
    - Request metadata (method, path, client IP)
    - Response status and duration
    - Errors and exceptions

    Usage in main.py:
        from fastapi import FastAPI
        from opik.middleware import OpikMiddleware

        app = FastAPI()
        app.add_middleware(OpikMiddleware)

    Example:
        app = FastAPI(title="Raimon API")
        app.add_middleware(OpikMiddleware)

        @app.get("/health")
        async def health():
            return {"status": "ok"}
    """

    def __init__(self, app, exclude_paths: list[str] = None):
        """
        Initialize the middleware

        Args:
            app: The FastAPI application
            exclude_paths: List of paths to exclude from tracking (e.g., ["/health", "/metrics"])
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and track it with Opik

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the route handler
        """
        # Skip tracking for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Start tracking
        start_time = time.time()
        opik_client = get_opik_client()

        # Store request metadata
        request_data = {
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Track successful request
            print(
                f"📊 Request tracked: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration:.2f}s"
            )

            # You can add actual Opik tracking here
            # opik_client.opik.track_request(request_data, response.status_code, duration)

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Track failed request
            print(
                f"❌ Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Duration: {duration:.2f}s"
            )

            # You can add actual Opik error tracking here
            # opik_client.opik.track_error(request_data, str(e), duration)

            raise

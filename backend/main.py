from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import logging
import time

# Load environment variables
load_dotenv()

from routers import auth, users, projects, tasks, next_do, dashboard, analytics, notifications, reminders, integrations
from routers.agents import router as agents_router
from core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Raimon API",
    description="Backend API for Raimon - AI-powered productivity assistant",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS from environment
allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Request body size limit middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_request_body_size:
        return JSONResponse(
            status_code=413,
            content={
                "success": False,
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "Request body too large",
                },
            },
        )
    return await call_next(request)


# Audit logging middleware
@app.middleware("http")
async def audit_log(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Log auth-related requests
    if "/api/auth/" in request.url.path:
        logger.info(
            f"AUTH_AUDIT: {request.method} {request.url.path} "
            f"status={response.status_code} "
            f"ip={request.client.host if request.client else 'unknown'} "
            f"duration={duration:.3f}s"
        )
    # Log failed requests
    elif response.status_code >= 400:
        logger.warning(
            f"REQUEST_FAILED: {request.method} {request.url.path} "
            f"status={response.status_code} "
            f"ip={request.client.host if request.client else 'unknown'} "
            f"duration={duration:.3f}s"
        )

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        },
    )


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(next_do.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(reminders.router)
app.include_router(integrations.router)
app.include_router(agents_router)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "success": True,
        "message": "Raimon API is running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

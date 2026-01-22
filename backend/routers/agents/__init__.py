from fastapi import APIRouter
from . import (
    priority_engine,
    state_adapter,
    time_learning,
    stuck_pattern,
    project_insight,
    motivation,
    context_continuity,
    user_profile,
)

router = APIRouter(prefix="/api/agents", tags=["AI Agents"])

router.include_router(priority_engine.router)
router.include_router(state_adapter.router)
router.include_router(time_learning.router)
router.include_router(stuck_pattern.router)
router.include_router(project_insight.router)
router.include_router(motivation.router)
router.include_router(context_continuity.router)
router.include_router(user_profile.router)

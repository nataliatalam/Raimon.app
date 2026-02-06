"""
Application-level data models for Raimon.

Exports all Pydantic models for API contracts, database operations, and data flow.
"""

from models.contracts import (
    TaskCandidate,
    SelectionConstraints,
    DoSelectorOutput,
    CoachOutput,
    ActiveDo,
    WorkSession,
    UserProfile,
    DailyCheckIn,
    TimePatterns,
    MotivationMessage,
    GamificationState,
)

# Import other model modules
try:
    from models import auth, user, task, project, notification, next_do
except ImportError:
    # Some modules may not exist, that's okay
    pass

__all__ = [
    # Contracts (from agent_mvp)
    "TaskCandidate",
    "SelectionConstraints",
    "DoSelectorOutput",
    "CoachOutput",
    "ActiveDo",
    "WorkSession",
    "UserProfile",
    "DailyCheckIn",
    "TimePatterns",
    "MotivationMessage",
    "GamificationState",
]

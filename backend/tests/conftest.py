"""
Shared pytest configuration and fixtures for Raimon tests.

Provides common setup, fixtures, and utilities for all test suites.
"""

import pytest
import os
from typing import Generator, Dict, Any
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Load .env before any test module is collected (needed for module-level instantiations)
load_dotenv()


# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENV"] = "test"
    os.environ["JWT_SECRET_KEY"] = "standard-test-secret-key-32-chars"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"


# FastAPI test client
@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    from fastapi import FastAPI
    from middleware import setup_cors_middleware

    app = FastAPI()
    setup_cors_middleware(app)
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient

    return TestClient(test_app)


# Mock storage and agents
@pytest.fixture
def mock_storage() -> MagicMock:
    """Create a mock storage service."""
    storage = MagicMock()
    storage.get_task_candidates = MagicMock(return_value=[])
    storage.save_active_do = MagicMock()
    storage.get_session_state = MagicMock(return_value={})
    storage.update_session_status = MagicMock()
    storage.save_insights = MagicMock()
    return storage


@pytest.fixture
def mock_agents() -> Dict[str, MagicMock]:
    """Create mock agent instances."""
    return {
        "llm_do_selector": MagicMock(),
        "llm_coach": MagicMock(),
        "stuck_pattern_agent": MagicMock(),
        "motivation_agent": MagicMock(),
        "context_continuity_agent": MagicMock(),
        "user_profile_agent": MagicMock(),
        "state_adapter_agent": MagicMock(),
        "priority_engine_agent": MagicMock(),
    }


# Test data fixtures
@pytest.fixture
def sample_user_id() -> str:
    """Return a sample user ID for testing."""
    return "test-user-123"


@pytest.fixture
def sample_session_id() -> str:
    """Return a sample session ID for testing."""
    return "session-abc-456"


@pytest.fixture
def sample_app_open_event(sample_user_id):
    """Create a sample APP_OPEN event."""
    from models.contracts import AppOpenEvent

    return AppOpenEvent(user_id=sample_user_id)


@pytest.fixture
def sample_checkin_event(sample_user_id):
    """Create a sample CHECKIN_SUBMITTED event."""
    from models.contracts import CheckInSubmittedEvent

    return CheckInSubmittedEvent(
        user_id=sample_user_id,
        energy_level=7,
        mood="motivated",
        focus_areas=["work", "health"],
        time_available=120,
    )


@pytest.fixture
def sample_do_next_event(sample_user_id):
    """Create a sample DO_NEXT event."""
    from models.contracts import DoNextEvent

    return DoNextEvent(user_id=sample_user_id)


@pytest.fixture
def sample_do_action_event(sample_user_id):
    """Create a sample DO_ACTION event."""
    from models.contracts import DoActionEvent

    return DoActionEvent(
        user_id=sample_user_id,
        action="start",
        task_id="task-123",
        current_session={},
        time_stuck=0,
    )


@pytest.fixture
def sample_day_end_event(sample_user_id):
    """Create a sample DAY_END event."""
    from models.contracts import DayEndEvent

    return DayEndEvent(user_id=sample_user_id, timestamp=datetime.now(timezone.utc).isoformat())


@pytest.fixture
def sample_task_candidates() -> list:
    """Return sample task candidates."""
    return [
        {
            "id": "task-1",
            "title": "Complete project report",
            "priority": "high",
            "status": "todo",
            "estimated_duration": 60,
            "tags": ["work", "reporting"],
        },
        {
            "id": "task-2",
            "title": "Review team feedback",
            "priority": "medium",
            "status": "todo",
            "estimated_duration": 30,
            "tags": ["work", "feedback"],
        },
        {
            "id": "task-3",
            "title": "Exercise",
            "priority": "low",
            "status": "todo",
            "estimated_duration": 45,
            "tags": ["health", "exercise"],
        },
    ]


@pytest.fixture
def sample_constraints() -> Dict[str, Any]:
    """Return sample task selection constraints."""
    return {
        "max_minutes": 120,
        "mode": "balanced",
        "current_energy": 7,
        "avoid_tags": ["long_tasks"],
        "prefer_priority": "high",
    }


@pytest.fixture
def sample_graph_state(sample_user_id):
    """Create a sample GraphState for testing."""
    from orchestrator.contracts import GraphState

    return GraphState(
        user_id=sample_user_id,
        current_event=None,
        mood="motivated",
        energy_level=7,
        candidates=[],
        constraints={},
        active_do=None,
        success=True,
        error=None,
    )


# Mocking and patching utilities
@pytest.fixture
def mock_supabase(monkeypatch):
    """Mock Supabase client."""
    mock = MagicMock()
    mock.table = MagicMock(return_value=mock)
    mock.select = MagicMock(return_value=mock)
    mock.eq = MagicMock(return_value=mock)
    mock.execute = MagicMock(return_value=MagicMock(data=[]))
    monkeypatch.setattr("core.supabase.get_supabase", lambda: mock)
    return mock


@pytest.fixture
def mock_opik(monkeypatch):
    """Mock Opik tracing decorator."""

    def mock_track(*args, **kwargs):
        def decorator(func):
            return func

        if args and callable(args[0]):
            return args[0]
        return decorator

    monkeypatch.setattr("opik.track", mock_track)


# LLM Service fixtures
@pytest.fixture
def mock_llm_service():
    """Create a mocked LLM service for testing."""
    from services.llm_service import LLMService

    service = MagicMock(spec=LLMService)
    service.generate_json.return_value = {"status": "success", "result": "test"}
    service.generate_text.return_value = "mocked text response"
    service.get_client.return_value = MagicMock()
    service.set_client.return_value = None
    return service


@pytest.fixture
def llm_service():
    """Create a real LLM service for testing (requires GOOGLE_API_KEY)."""
    from services.llm_service import LLMService

    # Only create if API key is available
    if os.getenv("GOOGLE_API_KEY"):
        return LLMService()
    else:
        pytest.skip("GOOGLE_API_KEY not set, skipping real LLM service tests")


@pytest.fixture
def mock_gemini_client():
    """Create a mocked Gemini client."""
    from services.llm_service import GeminiClient

    client = MagicMock(spec=GeminiClient)
    client.generate_json_response.return_value = {"status": "success"}
    client.generate_text.return_value = "mocked gemini response"
    return client


# Cleanup fixtures
@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test."""
    from opik_utils.metrics import get_metrics_collector, get_task_selection_metrics, get_engagement_metrics

    yield

    # Reset after test
    collector = get_metrics_collector()
    for agent in collector.agents.values():
        agent.reset()

    metrics = get_task_selection_metrics()
    metrics.reset()

    engagement = get_engagement_metrics()
    engagement.reset()


# Utility functions
@pytest.fixture
def create_jwt_token():
    """Factory fixture to create JWT tokens for testing."""

    def _create_token(user_id: str, secret_key: str = "test-secret-key") -> str:
        from middleware.jwt_middleware import JWTMiddleware

        data = {"sub": user_id, "user_id": user_id}
        return JWTMiddleware.create_token(data, secret_key, expires_delta=3600)

    return _create_token


@pytest.fixture
def authorization_header(create_jwt_token):
    """Factory fixture to create Authorization headers."""

    def _create_header(user_id: str = "test-user-123") -> Dict[str, str]:
        token = create_jwt_token(user_id)
        return {"Authorization": f"Bearer {token}"}

    return _create_header


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "agent: Agent-specific tests")
    config.addinivalue_line("markers", "orchestrator: Orchestrator tests")
    config.addinivalue_line("markers", "router: Router/endpoint tests")


# Logging fixtures
@pytest.fixture
def caplog_debug(caplog):
    """Set caplog to DEBUG level."""
    with caplog.at_level("DEBUG"):
        yield caplog

"""
Tests for Opik trackers
"""
import pytest
import sys
import os
from pathlib import Path

# Megkeressük a backend mappát (a tests szülőjének a szülője)
backend_path = str(Path(__file__).resolve().parent.parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from opik_utils.trackers import AgentTracker, LLMTracker, WorkflowTracker


@pytest.mark.asyncio
async def test_agent_tracker_initialization():
    """Test AgentTracker initialization"""
    tracker = AgentTracker(agent_name="test_agent")
    assert tracker.agent_name == "test_agent"
    assert tracker.start_time is None


@pytest.mark.asyncio
async def test_agent_tracker_start():
    """Test AgentTracker start method"""
    tracker = AgentTracker(agent_name="test_agent")
    await tracker.start(input_data={"test": "data"})
    assert tracker.start_time is not None
    assert tracker.input_data == {"test": "data"}
    assert tracker.trace_id is not None


def test_llm_tracker_initialization():
    """Test LLMTracker initialization"""
    tracker = LLMTracker(model_name="gemini-2.0-flash")
    assert tracker.model_name == "gemini-2.0-flash"
    assert tracker.total_tokens == 0
    assert tracker.total_cost == 0.0


@pytest.mark.asyncio
async def test_llm_tracker_generation():
    """Test LLMTracker track_generation method"""
    tracker = LLMTracker(model_name="gemini-2.0-flash")
    await tracker.track_generation(
        prompt="Test prompt",
        response="Test response",
        tokens_used=100
    )
    assert tracker.total_tokens == 100
    assert tracker.total_cost > 0


@pytest.mark.asyncio
async def test_workflow_tracker_initialization():
    """Test WorkflowTracker initialization"""
    tracker = WorkflowTracker(workflow_name="test_workflow")
    assert tracker.workflow_name == "test_workflow"
    assert tracker.status == "not_started"
    assert len(tracker.steps) == 0


@pytest.mark.asyncio
async def test_workflow_tracker_flow():
    """Test complete workflow tracking flow"""
    tracker = WorkflowTracker(workflow_name="test_workflow")

    await tracker.start()
    assert tracker.status == "running"
    assert tracker.start_time is not None

    tracker.add_step("step1", {"data": "value1"})
    tracker.add_step("step2", {"data": "value2"})
    assert len(tracker.steps) == 2

    await tracker.complete()
    assert tracker.status == "completed"
    assert tracker.end_time is not None

    summary = tracker.get_summary()
    assert summary["total_steps"] == 2
    assert summary["status"] == "completed"

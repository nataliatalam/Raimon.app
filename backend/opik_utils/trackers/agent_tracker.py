"""
Specialized tracker for agent execution and performance
"""
from typing import Dict, Any, Optional
import time
from datetime import datetime
from opik_utils.client import get_opik_client


class AgentTracker:
    """
    Track agent execution and performance

    Usage:
        tracker = AgentTracker(agent_name="priority_engine")
        await tracker.start(input_data={"task_id": "123"})
        # ... agent execution ...
        await tracker.complete(output_data={"priority": "high"})

    Example:
        async def run_priority_agent(task_data: dict):
            tracker = AgentTracker("priority_engine")
            await tracker.start(input_data=task_data)

            try:
                result = await analyze_priority(task_data)
                await tracker.complete(output_data=result)
                return result
            except Exception as e:
                await tracker.error(error=e)
                raise
    """

    def __init__(self, agent_name: str):
        """
        Initialize the agent tracker

        Args:
            agent_name: Name of the agent being tracked
        """
        self.agent_name = agent_name
        self.opik_client = get_opik_client()
        self.start_time: Optional[float] = None
        self.input_data: Optional[Dict[str, Any]] = None
        self.output_data: Optional[Dict[str, Any]] = None
        self.trace_id: Optional[str] = None

    async def start(self, input_data: Dict[str, Any]) -> None:
        """
        Track the start of an agent execution

        Args:
            input_data: Input data for the agent
        """
        self.start_time = time.time()
        self.input_data = input_data
        self.trace_id = f"{self.agent_name}_{int(self.start_time)}"

        print(f"🤖 Agent started: {self.agent_name} (Trace ID: {self.trace_id})")

    async def complete(self, output_data: Dict[str, Any]) -> None:
        """
        Track the successful completion of an agent

        Args:
            output_data: Output data from the agent
        """
        if self.start_time is None:
            raise ValueError("Agent tracker not started. Call start() first.")

        duration = time.time() - self.start_time
        self.output_data = output_data

        print(
            f"✅ Agent completed: {self.agent_name} - "
            f"Duration: {duration:.2f}s (Trace ID: {self.trace_id})"
        )

        # You can add actual Opik tracking here
        # self.opik_client.opik.log_trace(...)

    async def error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track agent errors

        Args:
            error: The exception that occurred
            context: Additional context about the error
        """
        if self.start_time is None:
            raise ValueError("Agent tracker not started. Call start() first.")

        duration = time.time() - self.start_time

        print(
            f"❌ Agent failed: {self.agent_name} - "
            f"Error: {str(error)} - Duration: {duration:.2f}s (Trace ID: {self.trace_id})"
        )

        # You can add actual Opik error tracking here
        # self.opik_client.opik.log_error(...)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the agent execution

        Returns:
            Dict: Metrics including duration, input/output sizes, etc.
        """
        if self.start_time is None:
            return {}

        duration = time.time() - self.start_time if self.output_data is None else None

        return {
            "agent_name": self.agent_name,
            "trace_id": self.trace_id,
            "duration": duration,
            "input_size": len(str(self.input_data)) if self.input_data else 0,
            "output_size": len(str(self.output_data)) if self.output_data else 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

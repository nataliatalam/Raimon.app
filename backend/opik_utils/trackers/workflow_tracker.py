"""
Track multi-step workflows with Opik
"""
from typing import List, Dict, Any, Optional
import time
from datetime import datetime, timezone
from opik_utils.client import get_opik_client


class WorkflowStep:
    """Represents a single step in a workflow"""

    def __init__(self, name: str, data: Dict[str, Any]):
        self.name = name
        self.data = data
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.duration: Optional[float] = None
        self.status: str = "pending"  # pending, running, completed, failed


class WorkflowTracker:
    """
    Track multi-step workflows

    Usage:
        tracker = WorkflowTracker(workflow_name="task_analysis")
        await tracker.start()

        tracker.add_step("fetch_task", {"task_id": "123"})
        tracker.add_step("analyze_priority", {"priority_score": 0.85})
        tracker.add_step("generate_insights", {"insights": [...]})

        await tracker.complete()

    Example:
        async def analyze_task_workflow(task_id: str):
            tracker = WorkflowTracker("task_analysis")
            await tracker.start()

            # Step 1
            task = await fetch_task(task_id)
            tracker.add_step("fetch_task", {"task": task})

            # Step 2
            priority = await analyze_priority(task)
            tracker.add_step("analyze_priority", {"priority": priority})

            # Step 3
            insights = await generate_insights(task, priority)
            tracker.add_step("generate_insights", {"insights": insights})

            await tracker.complete()
            return {"task": task, "priority": priority, "insights": insights}
    """

    def __init__(self, workflow_name: str):
        """
        Initialize the workflow tracker

        Args:
            workflow_name: Name of the workflow being tracked
        """
        self.workflow_name = workflow_name
        self.opik_client = get_opik_client()
        self.steps: List[WorkflowStep] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.status: str = "not_started"  # not_started, running, completed, failed
        self.trace_id: Optional[str] = None

    async def start(self) -> None:
        """Start tracking the workflow"""
        self.start_time = time.time()
        self.status = "running"
        self.trace_id = f"{self.workflow_name}_{int(self.start_time)}"

        print(f"🔄 Workflow started: {self.workflow_name} (Trace ID: {self.trace_id})")

    def add_step(
        self,
        step_name: str,
        data: Dict[str, Any],
        status: str = "completed"
    ) -> None:
        """
        Add a step to the workflow

        Args:
            step_name: Name of the step
            data: Data associated with the step
            status: Status of the step (completed, failed)
        """
        step = WorkflowStep(name=step_name, data=data)
        step.status = status
        self.steps.append(step)

        print(f"  📍 Step added: {step_name} - Status: {status}")

    async def complete(self) -> None:
        """Mark workflow as complete and send to Opik"""
        if self.start_time is None:
            raise ValueError("Workflow not started. Call start() first.")

        self.end_time = time.time()
        self.status = "completed"
        duration = self.end_time - self.start_time

        print(
            f"✅ Workflow completed: {self.workflow_name} - "
            f"Steps: {len(self.steps)} - Duration: {duration:.2f}s (Trace ID: {self.trace_id})"
        )

        # You can add actual Opik tracking here
        # self.opik_client.opik.log_workflow(...)

    async def fail(self, error: Exception) -> None:
        """Mark workflow as failed"""
        if self.start_time is None:
            raise ValueError("Workflow not started. Call start() first.")

        self.end_time = time.time()
        self.status = "failed"
        duration = self.end_time - self.start_time

        print(
            f"❌ Workflow failed: {self.workflow_name} - "
            f"Error: {str(error)} - Duration: {duration:.2f}s (Trace ID: {self.trace_id})"
        )

        # You can add actual Opik error tracking here
        # self.opik_client.opik.log_workflow_error(...)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the workflow execution

        Returns:
            Dict: Summary including steps, duration, status, etc.
        """
        duration = None
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time

        return {
            "workflow_name": self.workflow_name,
            "trace_id": self.trace_id,
            "status": self.status,
            "steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "timestamp": step.timestamp,
                }
                for step in self.steps
            ],
            "total_steps": len(self.steps),
            "duration": duration,
            "started_at": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "completed_at": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
        }

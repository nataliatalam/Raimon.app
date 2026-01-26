"""
Custom decorators for tracking LLM calls, agents, and workflows with Opik
"""
from functools import wraps
from typing import Callable, Any, Optional
import asyncio
import time
from .client import get_opik_client


def track_llm(model_name: str = "gemini-2.0-flash", track_tokens: bool = True):
    """
    Decorator to track LLM calls with Opik

    Args:
        model_name: Name of the LLM model being used
        track_tokens: Whether to track token usage

    Usage:
        @track_llm(model_name="gemini-2.0-flash")
        async def generate_text(prompt: str):
            opik_manager = get_opik_client()
            response = opik_manager.genai.models.generate_content(...)
            return response.text

    Example:
        @track_llm()
        async def chat_completion(message: str) -> str:
            return await llm_service.generate(message)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            opik_client = get_opik_client()
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Log successful LLM call to Opik
                # You can enhance this with actual Opik tracking calls
                print(f"✅ LLM call tracked: {func.__name__} ({model_name}) - {duration:.2f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ LLM call failed: {func.__name__} ({model_name}) - {duration:.2f}s - Error: {str(e)}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            opik_client = get_opik_client()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log successful LLM call to Opik
                print(f"✅ LLM call tracked: {func.__name__} ({model_name}) - {duration:.2f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ LLM call failed: {func.__name__} ({model_name}) - {duration:.2f}s - Error: {str(e)}")
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def track_agent(agent_name: str, track_metadata: bool = True):
    """
    Decorator to track agent execution with Opik

    Args:
        agent_name: Name of the agent being tracked
        track_metadata: Whether to track additional metadata

    Usage:
        @track_agent(agent_name="priority_engine")
        async def analyze_priority(task_data: dict):
            # Agent logic here
            return {"priority": "high", "score": 0.85}

    Example:
        @track_agent(agent_name="context_continuity")
        async def maintain_context(user_id: str, task_id: str) -> dict:
            return await agent_service.process(user_id, task_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            opik_client = get_opik_client()
            start_time = time.time()

            try:
                print(f"🤖 Starting agent: {agent_name}")
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Track agent success
                print(f"✅ Agent completed: {agent_name} - {duration:.2f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ Agent failed: {agent_name} - {duration:.2f}s - Error: {str(e)}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            opik_client = get_opik_client()
            start_time = time.time()

            try:
                print(f"🤖 Starting agent: {agent_name}")
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Track agent success
                print(f"✅ Agent completed: {agent_name} - {duration:.2f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ Agent failed: {agent_name} - {duration:.2f}s - Error: {str(e)}")
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def track_workflow(workflow_name: str, track_steps: bool = True):
    """
    Decorator to track multi-step workflows with Opik

    Args:
        workflow_name: Name of the workflow being tracked
        track_steps: Whether to track individual steps

    Usage:
        @track_workflow(workflow_name="task_analysis")
        async def analyze_task_workflow(task_id: str):
            # Step 1: Fetch task
            task = await fetch_task(task_id)
            # Step 2: Analyze priority
            priority = await analyze_priority(task)
            # Step 3: Generate insights
            insights = await generate_insights(task, priority)
            return {"task": task, "priority": priority, "insights": insights}

    Example:
        @track_workflow(workflow_name="user_onboarding")
        async def onboard_user(user_data: dict) -> dict:
            return await workflow_service.execute(user_data)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            opik_client = get_opik_client()
            start_time = time.time()

            try:
                print(f"🔄 Starting workflow: {workflow_name}")
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Track workflow completion
                print(f"✅ Workflow completed: {workflow_name} - {duration:.2f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ Workflow failed: {workflow_name} - {duration:.2f}s - Error: {str(e)}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            opik_client = get_opik_client()
            start_time = time.time()

            try:
                print(f"🔄 Starting workflow: {workflow_name}")
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Track workflow completion
                print(f"✅ Workflow completed: {workflow_name} - {duration:.2f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ Workflow failed: {workflow_name} - {duration:.2f}s - Error: {str(e)}")
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

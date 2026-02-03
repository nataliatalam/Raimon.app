"""
Project Insight Agent - Bounded insight generation.

Functionality: Generate insights about project progress and productivity patterns.

Inputs: ProjectInsightRequest { project_id, insight_type: str, time_range: str }

Outputs: ProjectInsights { insights: List[Insight], generated_at }

Memory:
- reads: projects, tasks, work_sessions, daily_check_ins
- writes: ai_learning_data (agent_type=project_insights)

LLM: YES (bounded insight generation)

Critical guarantees:
- insights are factual and based on data
- bounded output (max 5 insights, each <200 chars)
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from agent_mvp.contracts import (
    ProjectInsightRequest,
    ProjectInsights,
    Insight,
)
from agent_mvp.storage import get_project_data, get_project_tasks, get_project_sessions, get_project_checkins, save_ai_learning
from agent_mvp.gemini_client import GeminiClient
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="project_insight_agent")
def generate_project_insights(
    user_id: str,
    request: ProjectInsightRequest,
) -> ProjectInsights:
    """
    Generate bounded insights about project.

    Args:
        user_id: User UUID
        request: Insight request

    Returns:
        Project insights
    """
    logger.info(f"💡 Generating insights for project {request.project_id}")

    # Gather project data
    project = get_project_data(request.project_id, user_id)
    if not project:
        raise ValueError(f"Project {request.project_id} not found")

    tasks = get_project_tasks(request.project_id)
    sessions = get_project_sessions(request.project_id)
    checkins = get_project_checkins(request.project_id, days=30)

    # Generate insights based on type
    if request.insight_type == "progress":
        insights = _generate_progress_insights(project, tasks, sessions)
    elif request.insight_type == "productivity":
        insights = _generate_productivity_insights(sessions, checkins)
    elif request.insight_type == "patterns":
        insights = _generate_pattern_insights(tasks, sessions)
    else:
        insights = _generate_general_insights(project, tasks, sessions)

    # Use LLM for final insight refinement (bounded)
    refined_insights = _refine_insights_with_llm(project, insights, request.insight_type)

    result = ProjectInsights(
        insights=refined_insights,
        generated_at=datetime.utcnow(),
    )

    # Save insights for learning
    _save_project_insights(user_id, request.project_id, result)

    logger.info(f"✅ Generated {len(result.insights)} insights for project {request.project_id}")
    return result


def _generate_progress_insights(
    project: Dict[str, Any],
    tasks: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
) -> List[Insight]:
    """Generate progress-based insights."""
    insights = []

    if not tasks:
        return [Insight(content="No tasks found for this project", category="progress", confidence=1.0)]

    # Completion rate
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    total = len(tasks)
    completion_rate = completed / total if total > 0 else 0

    if completion_rate < 0.3:
        insights.append(Insight(
            content=f"Project is {completion_rate:.1%} complete - focus on building momentum",
            category="progress",
            confidence=0.9,
        ))
    elif completion_rate > 0.8:
        insights.append(Insight(
            content=f"Project is {completion_rate:.1%} complete - nearing completion!",
            category="progress",
            confidence=0.9,
        ))

    # Time spent vs estimated
    total_estimated = sum(t.get("estimated_duration", 0) for t in tasks)
    total_actual = sum(s.get("duration_minutes", 0) for s in sessions)

    if total_estimated > 0:
        time_ratio = total_actual / total_estimated
        if time_ratio > 1.5:
            insights.append(Insight(
                content=f"Time spent is {time_ratio:.1f}x estimated - consider adjusting estimates",
                category="progress",
                confidence=0.8,
            ))

    return insights


def _generate_productivity_insights(
    sessions: List[Dict[str, Any]],
    checkins: List[Dict[str, Any]],
) -> List[Insight]:
    """Generate productivity-based insights."""
    insights = []

    if not sessions:
        return [Insight(content="No work sessions recorded yet", category="productivity", confidence=1.0)]

    # Session completion rate
    completed = sum(1 for s in sessions if s.get("completed_at"))
    completion_rate = completed / len(sessions)

    if completion_rate < 0.5:
        insights.append(Insight(
            content=f"Only {completion_rate:.1%} of sessions completed - identify blockers",
            category="productivity",
            confidence=0.8,
        ))

    # Average session duration
    durations = [s.get("duration_minutes", 0) for s in sessions]
    avg_duration = sum(durations) / len(durations) if durations else 0

    if avg_duration < 25:
        insights.append(Insight(
            content=f"Average session is only {avg_duration:.0f} minutes - try longer focused blocks",
            category="productivity",
            confidence=0.7,
        ))

    # Energy correlation
    if checkins:
        high_energy_sessions = [s for s in sessions if _get_session_energy(s, checkins) >= 4]
        high_energy_completion = sum(1 for s in high_energy_sessions if s.get("completed_at"))
        high_energy_rate = high_energy_completion / len(high_energy_sessions) if high_energy_sessions else 0

        if high_energy_rate > completion_rate + 0.2:
            insights.append(Insight(
                content="Much more productive on high-energy days - prioritize rest",
                category="productivity",
                confidence=0.8,
            ))

    return insights


def _generate_pattern_insights(
    tasks: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
) -> List[Insight]:
    """Generate pattern-based insights."""
    insights = []

    # Task priority distribution
    priorities = {}
    for task in tasks:
        pri = task.get("priority", "medium")
        priorities[pri] = priorities.get(pri, 0) + 1

    if priorities.get("high", 0) > len(tasks) * 0.6:
        insights.append(Insight(
            content="Most tasks are high priority - consider reprioritizing",
            category="patterns",
            confidence=0.8,
        ))

    # Session timing patterns
    if sessions:
        hours = [s.get("start_time", {}).get("hour", 9) for s in sessions]
        peak_hour = max(set(hours), key=hours.count) if hours else 9

        insights.append(Insight(
            content=f"Most productive around {peak_hour}:00 - schedule important work then",
            category="patterns",
            confidence=0.7,
        ))

    return insights


def _generate_general_insights(
    project: Dict[str, Any],
    tasks: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
) -> List[Insight]:
    """Generate general project insights."""
    insights = []

    # Project age vs progress
    created = project.get("created_at")
    if created:
        try:
            age_days = (datetime.utcnow() - datetime.fromisoformat(created.replace('Z', '+00:00'))).days
            if age_days > 30 and len(tasks) == 0:
                insights.append(Insight(
                    content="Project created over a month ago but no tasks - time to break it down?",
                    category="general",
                    confidence=0.9,
                ))
        except:
            pass

    # Session frequency
    if sessions:
        session_dates = set()
        for s in sessions:
            start = s.get("start_time")
            if start:
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    session_dates.add(dt.date())
                except:
                    pass

        if len(session_dates) >= 7:  # Worked at least 7 different days
            insights.append(Insight(
                content="Consistent work pattern - keep up the momentum!",
                category="general",
                confidence=0.8,
            ))

    return insights


def _refine_insights_with_llm(
    project: Dict[str, Any],
    base_insights: List[Insight],
    insight_type: str,
) -> List[Insight]:
    """Use LLM to refine and enhance insights."""
    if not base_insights:
        return []

    try:
        client = GeminiClient()

        prompt = f"""
        Project: {project.get('name', 'Unknown')}
        Insight type: {insight_type}

        Base insights:
        {chr(10).join(f"- {i.content}" for i in base_insights[:3])}

        Generate up to 3 refined insights that are:
        - Factual and data-driven
        - Actionable and specific
        - Under 150 characters each
        - Focused on {insight_type} aspects

        Return as JSON array of strings.
        """

        response = client.generate_json_response(prompt, max_tokens=300)

        if isinstance(response, list) and response:
            refined = []
            for item in response[:3]:
                if isinstance(item, str) and len(item) <= 150:
                    refined.append(Insight(
                        content=item,
                        category=insight_type,
                        confidence=0.85,  # LLM-refined insights get higher confidence
                    ))
            return refined

    except Exception as e:
        logger.warning(f"⚠️ LLM insight refinement failed: {str(e)}")

    # Return base insights if LLM fails
    return base_insights[:3]


def _get_session_energy(session: Dict[str, Any], checkins: List[Dict[str, Any]]) -> int:
    """Get energy level for a session based on nearby check-ins."""
    session_time = session.get("start_time")
    if not session_time:
        return 3  # Default

    try:
        session_dt = datetime.fromisoformat(session_time.replace('Z', '+00:00'))

        # Find closest check-in within 2 hours
        closest_energy = 3
        min_diff = timedelta(hours=2)

        for checkin in checkins:
            checkin_time = checkin.get("created_at")
            if checkin_time:
                checkin_dt = datetime.fromisoformat(checkin_time.replace('Z', '+00:00'))
                diff = abs(session_dt - checkin_dt)
                if diff < min_diff:
                    min_diff = diff
                    closest_energy = checkin.get("energy_level", 3)

        return closest_energy
    except:
        return 3


def _save_project_insights(user_id: str, project_id: str, insights: ProjectInsights) -> None:
    """Save insights for learning."""
    try:
        save_ai_learning(
            user_id=user_id,
            agent_type="project_insights",
            data={
                "project_id": project_id,
                "insights": [i.model_dump() for i in insights.insights],
                "generated_at": insights.generated_at.isoformat(),
            },
            expires_at=datetime.utcnow() + timedelta(days=7),  # Refresh weekly
        )
        logger.info(f"💾 Saved project insights for user {user_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to save project insights: {str(e)}")
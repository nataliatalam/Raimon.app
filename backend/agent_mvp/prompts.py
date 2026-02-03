"""
LLM prompt templates for agent MVP.
Keep prompts short, bounded, and clear.
"""

from typing import List, Optional, Dict, Any
from agent_mvp.contracts import TaskCandidate, SelectionConstraints


def build_do_selector_prompt(
    candidates: List[TaskCandidate],
    constraints: SelectionConstraints,
    recent_actions: Optional[dict] = None,
) -> str:
    """
    Build prompt for DoSelector agent.

    Returns a prompt that results in JSON-only output.
    """

    # Build candidate list
    candidates_text = ""
    for i, task in enumerate(candidates, 1):
        candidates_text += f"""
{i}. Task ID: {task.id}
   Title: {task.title}
   Priority: {task.priority}
   Est. Duration: {task.estimated_duration or '?'} min
   Due: {task.due_at.isoformat() if task.due_at else 'No deadline'}
   Tags: {', '.join(task.tags) if task.tags else 'None'}
"""

    prompt = f"""You are a task selection agent. Select ONE task from the list below that best fits the user's current state.

CANDIDATES:
{candidates_text}

CONSTRAINTS:
- Max time available: {constraints.max_minutes} minutes
- Current energy level: {constraints.current_energy}/10
- Mode: {constraints.mode} (focus=deep work, quick=under 30min, learning=new skills, balanced=mix)
- Avoid tags: {', '.join(constraints.avoid_tags) if constraints.avoid_tags else 'None'}
- Prefer priority: {constraints.prefer_priority or 'Any'}

RULES:
1. Select exactly ONE task_id from the candidates above
2. ONLY include reason_codes that apply (max 3)
3. Include 0-2 alternative task IDs
4. Never invent task details; use provided data only

REASON CODES (use only these):
- deadline_urgent (due within 24h)
- deadline_soon (due within 3 days)
- priority_high (marked urgent/high)
- priority_medium (marked medium)
- energy_fit (matches current energy)
- time_fit (fits time constraint)
- mode_fit (aligns with selected mode)
- progress_continuation (task already started)

Respond with ONLY valid JSON matching this format:
{{
  "task_id": "<one of the candidate IDs above>",
  "reason_codes": ["code1", "code2"],
  "alt_task_ids": ["<id2>", "<id3>"]
}}

No explanation. JSON only."""

    return prompt


def build_coach_prompt(
    task: TaskCandidate,
    reason_codes: List[str],
    mode: str = "balanced",
    user_name: Optional[str] = None,
) -> str:
    """
    Build prompt for Coach agent.

    Returns a prompt that results in JSON-only output.
    """

    greeting = f"Hey {user_name}," if user_name else "Here's your next move:"

    prompt = f"""{greeting}

You are a brief, motivational coach. Provide a short encouragement message for this task:

TASK:
- Title: {task.title}
- Priority: {task.priority}
- Est. Duration: {task.estimated_duration or '?'} min
- Why selected: {', '.join(reason_codes)}
- Mode: {mode}

RULES:
1. "title": 1 short motivational phrase (under 10 words)
2. "message": 1-2 sentences max, encouraging but realistic
3. "next_step": 1 micro-action under 10 words (start with verb)
4. Never invent task details beyond what's provided
5. Keep it short and actionable

Respond with ONLY valid JSON:
{{
  "title": "<motivational phrase>",
  "message": "<1-2 sentence encouragement>",
  "next_step": "<micro-action under 10 words>"
}}

No explanation. JSON only."""

    return prompt


def build_project_suggestions_prompt(normalized_data: Dict[str, Any]) -> str:
    """
    Build prompt for project profile suggestions.
    """
    prompt = f"""
    Analyze this project profile and provide up to 3 specific, actionable suggestions for improvement.
    Focus on productivity, organization, or completion strategies.

    Project Data:
    {normalized_data}

    Return JSON array of suggestions, each with "category", "suggestion", "impact" (high/medium/low).
    Keep each suggestion under 100 characters.
    """

    return prompt


def build_stuck_microtasks_prompt(
    task_title: str,
    time_spent: int,
    context: str = "general",
) -> str:
    """
    Build prompt for stuck pattern microtasks.
    """
    prompt = f"""
    A user is stuck on this task: "{task_title}"
    They have been working for {time_spent} minutes.

    Generate 3 specific, actionable microtasks (1-2 minutes each) to help them get unstuck.
    Make them concrete and immediately actionable.

    Base these on common getting-unstuck strategies but tailor to the task if possible.

    Return as JSON array of strings, each under 100 characters.
    """

    return prompt


def build_project_insights_prompt(
    project_data: Dict[str, Any],
    insight_type: str,
) -> str:
    """
    Build prompt for project insights generation.
    """
    prompt = f"""
    Project: {project_data.get('name', 'Unknown')}
    Insight type: {insight_type}

    Project Data:
    {project_data}

    Generate up to 3 refined insights that are:
    - Factual and data-driven
    - Actionable and specific
    - Under 150 characters each
    - Focused on {insight_type} aspects

    Return as JSON array of strings.
    """

    return prompt


def build_motivation_prompt(
    user_data: Dict[str, Any],
    tone: str,
    context: str,
) -> str:
    """
    Build prompt for motivation message generation.
    """
    prompt = f"""
    Generate a short, encouraging motivation message based on this user data:

    Context: {context}
    Current streak: {user_data.get('current_streak', 0)} days
    Level: {user_data.get('level', 1)}
    Recent completion rate: {user_data.get('completion_rate', 0):.1%}
    Sessions today: {user_data.get('recent_sessions', 0)}

    Tone: {tone} (encouraging, positive, supportive)

    Requirements:
    - Under 150 characters
    - Positive and encouraging
    - Personalized to their progress
    - End with actionable encouragement

    Return only the message text, no quotes or extra formatting.
    """

    return prompt

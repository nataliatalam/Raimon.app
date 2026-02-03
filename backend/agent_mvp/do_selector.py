"""
Do Selector - Deterministic core task selection.

Functionality: Select optimal task from scored candidates based on constraints.

Inputs: DoSelectionRequest { scored_candidates: List[TaskCandidateWithScore], constraints: SelectionConstraints }

Outputs: DoSelection { selected_task: TaskCandidateWithScore, selection_reason: str }

Memory:
- reads: NONE (pure function)
- writes: NONE (pure function)

LLM: NO (deterministic selection algorithm)

Critical guarantees:
- deterministic selection based on fixed algorithm
- always selects highest-scoring task that fits constraints
- fallback to any task if no perfect fit
"""

from typing import List, Dict, Any
from types import SimpleNamespace
from core.supabase import get_supabase
from agent_mvp.contracts import (
    DoSelectorInput,
    DoSelectorOutput,
    TaskCandidate,
    TaskCandidateScored,
    TaskCandidateWithScore,
    SelectionConstraints,
    PriorityCandidates,
    SelectionResult,
    UserProfile,
    CheckInConstraints,
    DoSelectionRequest,
    DoSelection,
)
from agent_mvp import storage
from opik import track
import logging

logger = logging.getLogger(__name__)


@track(name="do_selector")
def select_optimal_task(
    request: DoSelectionRequest,
) -> DoSelection:
    """
    Select optimal task from scored candidates.

    Args:
        request: Selection request with candidates and constraints

    Returns:
        Task selection with reasoning
    """
    logger.info(f"🎯 Selecting from {len(request.scored_candidates)} candidates")

    if not request.scored_candidates:
        raise ValueError("No task candidates provided")

    # Filter candidates that fit constraints
    fitting_candidates = _filter_by_constraints(request.scored_candidates, request.constraints)

    if fitting_candidates:
        # Select highest scoring from fitting candidates
        selected = max(fitting_candidates, key=lambda c: c.priority_score)
        reason = "Selected highest-scoring task that fits all constraints"
    else:
        # Fallback: select highest scoring overall, even if constraints not perfectly met
        selected = max(request.scored_candidates, key=lambda c: c.priority_score)
        reason = "No tasks perfectly fit constraints - selected highest-scoring option"

    # Add constraint-specific reasoning
    detailed_reason = _build_detailed_reason(selected, request.constraints, reason)

    selection = DoSelection(
        selected_task=selected,
        selection_reason=detailed_reason,
    )

    logger.info(f"✅ Selected task: {selected.task.get('title', 'Unknown')} (score: {selected.priority_score:.1f})")
    return selection


def _filter_by_constraints(
    candidates: List[TaskCandidateWithScore],
    constraints: SelectionConstraints,
) -> List[TaskCandidateWithScore]:
    """Filter candidates that fit all constraints."""
    fitting = []

    for candidate in candidates:
        task = candidate.task

        # Check time constraint
        task_duration = task.get("estimated_duration", 60)
        if task_duration > constraints.max_task_duration:
            continue

        # Check energy constraint
        task_energy_req = _estimate_energy_requirement(task)
        if task_energy_req > constraints.energy_level:
            continue

        # Check focus area constraint
        task_tags = set(task.get("tags", []))
        task_categories = _extract_categories(task)
        focus_match = bool(task_tags & set(constraints.focus_areas)) or bool(task_categories & set(constraints.focus_areas))

        if constraints.focus_areas and not focus_match:
            continue

        # Check blocked categories
        if any(cat in constraints.blocked_categories for cat in task_categories):
            continue

        fitting.append(candidate)

    return fitting


def _estimate_energy_requirement(task: Dict[str, Any]) -> int:
    """Estimate energy level required for task."""
    priority = task.get("priority", "medium")
    complexity = task.get("complexity", "medium")
    duration = task.get("estimated_duration", 60)

    # Base energy requirement
    energy_map = {
        "low": 1,
        "medium": 3,
        "high": 4,
        "urgent": 5,
    }
    base_energy = energy_map.get(priority, 3)

    # Adjust for complexity
    if complexity == "high":
        base_energy += 1
    elif complexity == "low":
        base_energy -= 1

    # Adjust for duration
    if duration > 120:  # Over 2 hours
        base_energy += 1
    elif duration < 30:  # Under 30 min
        base_energy -= 1

    return max(1, min(5, base_energy))


def _extract_categories(task: Dict[str, Any]) -> List[str]:
    """Extract category keywords from task."""
    categories = []

    # From tags
    tags = task.get("tags", [])
    categories.extend(tags)

    # From title/description keywords
    title = task.get("title", "").lower()
    description = task.get("description", "").lower()

    text = f"{title} {description}"

    category_keywords = {
        "work": ["work", "professional", "job", "career"],
        "personal": ["personal", "home", "family", "house"],
        "health": ["health", "fitness", "exercise", "medical"],
        "learning": ["learn", "study", "course", "education", "skill"],
        "creative": ["creative", "art", "design", "write", "music"],
        "social": ["social", "meeting", "call", "community", "friend"],
        "maintenance": ["maintenance", "admin", "organize", "clean"],
    }

    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            categories.append(category)

    return list(set(categories))  # Remove duplicates


def _build_detailed_reason(
    selected: TaskCandidateWithScore,
    constraints: SelectionConstraints,
    base_reason: str,
) -> str:
    """Build detailed selection reasoning."""
    reasons = [base_reason]

    task = selected.task

    # Time fit
    duration = task.get("estimated_duration", 60)
    if duration <= constraints.max_task_duration:
        reasons.append(f"Duration ({duration}min) fits available time")
    else:
        reasons.append(f"Duration ({duration}min) exceeds limit but selected as best option")

    # Energy fit
    energy_req = _estimate_energy_requirement(task)
    if energy_req <= constraints.energy_level:
        reasons.append(f"Energy requirement ({energy_req}) matches current level ({constraints.energy_level})")
    else:
        reasons.append(f"Energy requirement ({energy_req}) higher than current level ({constraints.energy_level})")

    # Focus alignment
    task_categories = _extract_categories(task)
    focus_match = bool(set(task_categories) & set(constraints.focus_areas))
    if constraints.focus_areas:
        if focus_match:
            reasons.append(f"Aligns with focus areas: {', '.join(constraints.focus_areas)}")
        else:
            reasons.append("Doesn't match focus areas but selected for priority")

    # Priority score
    reasons.append(f"Priority score: {selected.priority_score:.1f}/100")

    return " | ".join(reasons)


# Export class wrapper for test compatibility
class DoSelector:
    """Wrapper class for do_selector module for backward compatibility with tests."""

    def __init__(self) -> None:
        self.storage = storage

    def _calculate_energy_alignment(self, current_energy: int, estimated_duration: int) -> float:
        """Score alignment between energy and task duration."""
        energy_score = max(0.0, min(1.0, current_energy / 10))
        duration_penalty = max(0.0, min(1.0, estimated_duration / 120))
        score = (energy_score - (duration_penalty * 0.5)) * 100
        return max(0.0, min(100.0, score))

    def _calculate_context_match(self, task_tags: List[str], focus_areas: List[str]) -> float:
        """Score how well task tags match focus areas."""
        if not focus_areas:
            return 0.0
        overlap = set(task_tags) & set(focus_areas)
        ratio = len(overlap) / max(1, len(set(focus_areas)))
        return max(0.0, min(100.0, ratio * 100))

    def _calculate_task_score(
        self,
        candidate: TaskCandidate,
        user_profile: UserProfile,
        constraints: CheckInConstraints,
    ) -> float:
        """Calculate task score based on priority and context fit."""
        priority_map = {
            "high": 100.0,
            "medium": 70.0,
            "low": 40.0,
            "urgent": 120.0,
        }
        base = priority_map.get(candidate.priority, 50.0)

        duration = candidate.estimated_duration or 60
        energy_bonus = self._calculate_energy_alignment(constraints.energy_level, duration) * 0.2
        context_bonus = self._calculate_context_match(candidate.tags or [], constraints.focus_areas) * 0.3
        time_bonus = 10.0 if duration <= constraints.time_available else 0.0

        return float(base + energy_bonus + context_bonus + time_bonus)

    def _filter_candidates_by_constraints(
        self,
        candidates: List[TaskCandidate],
        constraints: CheckInConstraints,
    ) -> List[TaskCandidate]:
        """Filter candidates by time constraint."""
        filtered = []
        for candidate in candidates:
            # Only filter by time - duration must fit within available time
            duration = candidate.estimated_duration or 60
            if duration <= constraints.time_available:
                filtered.append(candidate)

        return filtered

    def _select_best_task(
        self,
        candidates: List[TaskCandidate],
        user_profile: UserProfile,
        constraints: CheckInConstraints,
    ) -> SimpleNamespace:
        """Select best task and return id/score for tests."""
        best_candidate = None
        best_score = -1.0
        for candidate in candidates:
            score = self._calculate_task_score(candidate, user_profile, constraints)
            if score > best_score:
                best_candidate = candidate
                best_score = score

        return SimpleNamespace(id=best_candidate.id, score=best_score, candidate=best_candidate)

    async def select_task(
        self,
        user_id: str,
        constraints: CheckInConstraints,
        candidates: PriorityCandidates,
    ) -> SelectionResult:
        """Full selection flow used by tests."""
        user_profile = self.storage.get_user_profile(user_id)
        if isinstance(user_profile, dict):
            user_profile = UserProfile(**user_profile)
        if user_profile is None:
            user_profile = UserProfile(user_id=user_id)

        candidate_list: List[TaskCandidate] = []
        for item in candidates.candidates:
            if isinstance(item, TaskCandidateScored):
                candidate_list.append(item.task)
            else:
                candidate_list.append(item)

        if not candidate_list:
            fallback_task = TaskCandidate(
                id="fallback",
                title="Quick win task",
                priority="low",
                estimated_duration=5,
            )
            return SelectionResult(
                task=fallback_task,
                selection_reason="No suitable tasks found; using a quick fallback task.",
                coaching_message="Start with something small to build momentum.",
            )

        filtered = self._filter_candidates_by_constraints(candidate_list, constraints)
        use_candidates = filtered if filtered else candidate_list
        best = self._select_best_task(use_candidates, user_profile, constraints)

        reason = "Selected best task based on priority, time fit, and context."
        coaching = f"Start with: {best.candidate.title}. You’ve got this."

        return SelectionResult(
            task=best.candidate,
            selection_reason=reason,
            coaching_message=coaching,
        )
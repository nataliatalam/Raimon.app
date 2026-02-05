"""
Do Selector - Deterministic core task selection.

Functionality: Select optimal task from scored candidates based on constraints.

Inputs: DoSelectorInput { candidates: List[TaskCandidate], constraints: SelectionConstraints }
Outputs: DoSelectorOutput { task_id, reason_codes, alt_task_ids }

Memory:
- reads: NONE (pure function)
- writes: NONE (pure function)

LLM: NO (deterministic selection algorithm)

Critical guarantees:
- deterministic selection based on fixed algorithm
- always selects a task
- fallback to best overall if no candidate fits constraints
- stable tie-breaking: (-score, duration, task_id)
"""

from __future__ import annotations

from typing import List, Dict, Any, Union
from types import SimpleNamespace
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

DEFAULT_DURATION_MINUTES = 60
MAX_DURATION_MINUTES = 1440
DEFAULT_ENERGY_REQUIREMENT = 3

ENERGY_ENUM_MAP = {
    "very_low": 1,
    "low": 2,
    "medium": 3,
    "med": 3,
    "high": 4,
    "very_high": 5,
    "extreme": 5,
}


def _get_task_value(task: Any, key: str, default: Any = None) -> Any:
    if isinstance(task, dict):
        return task.get(key, default)
    return getattr(task, key, default)


def _normalize_duration(task: Any) -> int:
    raw = _get_task_value(task, "estimated_minutes", None)
    if raw is None:
        raw = _get_task_value(task, "estimated_duration", None)
    if raw is None:
        raw = DEFAULT_DURATION_MINUTES
    try:
        duration = int(float(raw))
    except (TypeError, ValueError):
        duration = DEFAULT_DURATION_MINUTES
    return max(1, min(MAX_DURATION_MINUTES, duration))


def _normalize_energy(value: Any) -> int:
    if value is None:
        return DEFAULT_ENERGY_REQUIREMENT
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered.isdigit():
            try:
                value = int(lowered)
            except ValueError:
                value = DEFAULT_ENERGY_REQUIREMENT
        else:
            value = ENERGY_ENUM_MAP.get(lowered, DEFAULT_ENERGY_REQUIREMENT)
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        numeric = DEFAULT_ENERGY_REQUIREMENT
    return max(1, min(5, numeric))


def _get_task_energy_requirement(task: Any) -> int:
    raw = _get_task_value(task, "energy_req", None)
    if raw is None:
        raw = _get_task_value(task, "energy_requirement", None)
    if raw is None:
        raw = _get_task_value(task, "energy_level", None)
    if raw is None:
        raw = _get_task_value(task, "energy", None)
    if raw is None:
        return DEFAULT_ENERGY_REQUIREMENT
    return _normalize_energy(raw)


def _extract_task_id(task: Any) -> str:
    task_id = _get_task_value(task, "id", None)
    if not task_id or not str(task_id).strip():
        raise ValueError("Each task must have a stable id")
    return str(task_id)


def _get_candidate_task(candidate: Any) -> Any:
    if isinstance(candidate, TaskCandidateScored):
        return candidate.task
    if isinstance(candidate, TaskCandidate):
        return candidate
    if isinstance(candidate, dict) and "task" in candidate:
        return candidate["task"]
    if hasattr(candidate, "task"):
        return getattr(candidate, "task")
    return candidate


def _get_candidate_score(candidate: Any) -> float:
    if isinstance(candidate, TaskCandidateScored):
        return float(candidate.score)
    if hasattr(candidate, "score"):
        return float(getattr(candidate, "score"))
    if hasattr(candidate, "priority_score"):
        return float(getattr(candidate, "priority_score"))
    if isinstance(candidate, dict):
        if "score" in candidate:
            return float(candidate.get("score", 0.0))
        if "priority_score" in candidate:
            return float(candidate.get("priority_score", 0.0))
    return 0.0


def _get_candidate_reason_codes(candidate: Any) -> List[str]:
    if isinstance(candidate, TaskCandidateScored):
        return list(candidate.reason_codes)
    if hasattr(candidate, "reason_codes"):
        return list(getattr(candidate, "reason_codes"))
    if isinstance(candidate, dict):
        return list(candidate.get("reason_codes", []))
    return []


def _coerce_constraints(raw: Any) -> SelectionConstraints:
    if isinstance(raw, SelectionConstraints):
        constraints = raw
    elif raw is None:
        raise ValueError("Selection constraints are required")
    elif isinstance(raw, dict):
        constraints = SelectionConstraints(**raw)
    else:
        raise ValueError("Invalid selection constraints")

    if constraints.max_minutes is None:
        raise ValueError("Selection constraints must include max_minutes")
    try:
        constraints.max_minutes = int(float(constraints.max_minutes))
    except (TypeError, ValueError):
        raise ValueError("Selection constraints max_minutes must be int-like")
    if constraints.max_minutes <= 0:
        raise ValueError("Selection constraints max_minutes must be > 0")
    if constraints.current_energy is None:
        raise ValueError("Selection constraints must include current_energy")
    constraints.current_energy = _normalize_energy(constraints.current_energy)
    return constraints


def _summarize_constraints(constraints: SelectionConstraints, current_energy: int) -> Dict[str, Any]:
    return {
        "max_minutes": constraints.max_minutes,
        "current_energy": current_energy,
        "mode": constraints.mode,
        "avoid_tags": len(constraints.avoid_tags or []),
        "prefer_priority": constraints.prefer_priority,
    }


def _build_selection_reason(
    selected: Dict[str, Any],
    constraints: SelectionConstraints,
    current_energy: int,
    used_fallback: bool,
) -> str:
    duration = selected["duration"]
    energy_req = selected["energy_req"]
    score = selected["score"]

    parts = []
    if used_fallback:
        parts.append("No candidates fit constraints; selected best overall by score")
    else:
        parts.append("Selected highest-scoring task that fits constraints")

    parts.append(f"Score {score:.1f}")
    parts.append(f"Duration {duration}min (limit {constraints.max_minutes}min)")
    parts.append(f"Energy {energy_req} (current {current_energy})")

    return " | ".join(parts)


@track(name="do_selector")
def select_optimal_task(
    request: Union[DoSelectorInput, Dict[str, Any]],
) -> DoSelectorOutput:
    """
    Select optimal task from scored candidates.

    Args:
        request: Selection request with candidates and constraints

    Returns:
        DoSelectorOutput with selected task_id
    """
    if isinstance(request, DoSelectorInput):
        candidates = request.candidates
        if isinstance(candidates, PriorityCandidates):
            candidates = candidates.candidates
        constraints = _coerce_constraints(request.constraints)
        recent_actions = request.recent_actions or {}
        user_id = request.user_id
    else:
        candidates = request.get("candidates") or request.get("scored_candidates") or []
        if isinstance(candidates, PriorityCandidates):
            candidates = candidates.candidates
        constraints = _coerce_constraints(request.get("constraints"))
        recent_actions = request.get("recent_actions") or {}
        user_id = request.get("user_id", "")

    if not candidates:
        raise ValueError("No task candidates provided")

    current_energy = constraints.current_energy
    max_minutes = constraints.max_minutes

    trace_id = None
    if isinstance(recent_actions, dict):
        trace_id = recent_actions.get("trace_id")

    logger.info(
        "do_selector.start %s",
        {
            "trace_id": trace_id,
            "user_id": user_id,
            "n_candidates": len(candidates),
            "constraints": _summarize_constraints(constraints, current_energy),
        },
    )

    candidate_infos: List[Dict[str, Any]] = []
    for candidate in candidates:
        task = _get_candidate_task(candidate)
        task_id = _extract_task_id(task)
        duration = _normalize_duration(task)
        energy_req = _get_task_energy_requirement(task)
        score = _get_candidate_score(candidate)
        reason_codes = _get_candidate_reason_codes(candidate)

        candidate_infos.append(
            {
                "task_id": task_id,
                "task": task,
                "duration": duration,
                "energy_req": energy_req,
                "score": score,
                "reason_codes": reason_codes,
            }
        )

    def sort_key(item: Dict[str, Any]) -> tuple:
        return (-item["score"], item["duration"], item["task_id"])

    if not candidate_infos:
        fallback_task = _get_candidate_task(candidates[0]) if candidates else None
        if fallback_task is None:
            raise ValueError("No valid task candidates provided")
        fallback_id = _extract_task_id(fallback_task)
        return DoSelectorOutput(task_id=fallback_id, reason_codes=["fallback_direct"], alt_task_ids=[])

    fitting = [
        info
        for info in candidate_infos
        if info["duration"] <= max_minutes and info["energy_req"] <= current_energy
    ]

    selected_pool = fitting if fitting else candidate_infos
    selected_pool_sorted = sorted(selected_pool, key=sort_key)
    selected = selected_pool_sorted[0]

    overall_sorted = sorted(candidate_infos, key=sort_key)
    alt_task_ids = [
        info["task_id"]
        for info in overall_sorted
        if info["task_id"] != selected["task_id"]
    ][:2]

    task_priority = _get_task_value(selected["task"], "priority", None)
    used_fallback = not fitting

    reason_codes = []
    reason_codes.append("fallback_best_overall" if used_fallback else "constraints_fit")
    reason_codes.append("time_fit" if selected["duration"] <= max_minutes else "time_over")
    reason_codes.append(
        "energy_fit" if selected["energy_req"] <= current_energy else "energy_over"
    )
    if constraints.prefer_priority and task_priority == constraints.prefer_priority:
        reason_codes.append("priority_preferred")
    reason_codes = reason_codes[:5]

    top_candidates = sorted(candidate_infos, key=sort_key)[:3]
    candidate_summaries = [
        {
            "id": info["task_id"],
            "score": info["score"],
            "dur": info["duration"],
            "energy_req": info["energy_req"],
        }
        for info in top_candidates
    ]

    logger.info(
        "do_selector.end %s",
        {
            "trace_id": trace_id,
            "user_id": user_id,
            "chosen_task_id": selected["task_id"],
            "score": selected["score"],
            "duration": selected["duration"],
            "energy_req": selected["energy_req"],
            "reason_codes": reason_codes,
            "candidate_summaries": candidate_summaries,
        },
    )

    return DoSelectorOutput(
        task_id=selected["task_id"],
        reason_codes=reason_codes,
        alt_task_ids=alt_task_ids,
    )


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

        duration = candidate.estimated_duration or DEFAULT_DURATION_MINUTES
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
            duration = candidate.estimated_duration or DEFAULT_DURATION_MINUTES
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

        candidate_list: List[Any] = []
        for item in candidates.candidates:
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

        selection_constraints = SelectionConstraints(
            max_minutes=constraints.time_available,
            current_energy=constraints.energy_level,
            mode="balanced",
        )

        selection_output = select_optimal_task(
            DoSelectorInput(
                user_id=user_id,
                candidates=candidate_list,
                constraints=selection_constraints,
            )
        )

        selected_task = None
        selected_score = 0.0
        for item in candidate_list:
            task = _get_candidate_task(item)
            if _extract_task_id(task) == selection_output.task_id:
                selected_task = task
                selected_score = _get_candidate_score(item)
                break

        if selected_task is None:
            selected_task = _get_candidate_task(candidate_list[0])

        current_energy = _normalize_energy(selection_constraints.current_energy)
        duration = _normalize_duration(selected_task)
        energy_req = _get_task_energy_requirement(selected_task)
        used_fallback = not (duration <= selection_constraints.max_minutes and energy_req <= current_energy)

        selected_info = {
            "task_id": selection_output.task_id,
            "task": selected_task,
            "duration": duration,
            "energy_req": energy_req,
            "score": selected_score,
        }

        selection_reason = _build_selection_reason(
            selected=selected_info,
            constraints=selection_constraints,
            current_energy=current_energy,
            used_fallback=used_fallback,
        )

        selected_title = _get_task_value(selected_task, "title", "this task")
        coaching = f"Start with: {selected_title}. You’ve got this."

        return SelectionResult(
            task=selected_task,
            selection_reason=selection_reason,
            coaching_message=coaching,
        )


# Deterministic test snippet (example)
# def test_do_selector_determinism():
#     constraints = SelectionConstraints(max_minutes=60, current_energy=3)
#     candidates = [
#         TaskCandidateScored(task=TaskCandidate(id="b", title="Task B", estimated_duration=30), score=80),
#         TaskCandidateScored(task=TaskCandidate(id="a", title="Task A", estimated_duration=30), score=80),
#         TaskCandidateScored(task=TaskCandidate(id="c", title="Task C", estimated_duration=15), score=80),
#     ]
#     out1 = select_optimal_task({"user_id": "u1", "candidates": candidates, "constraints": constraints})
#     out2 = select_optimal_task({"user_id": "u1", "candidates": candidates, "constraints": constraints})
#     assert out1.task_id == out2.task_id == "c"
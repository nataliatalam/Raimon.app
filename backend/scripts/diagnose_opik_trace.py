"""
Refactored Opik Diagnostics - Test agent integration and tracing.

Run from repo root:
  powershell -ExecutionPolicy Bypass -File backend/scripts/run_opik_diagnose.ps1
  OR
  bash backend/scripts/run_tests.sh --diagnostics
  OR
  python backend/scripts/diagnose_opik_trace.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any
from datetime import datetime, timezone

from agents.deterministic_agents.do_selector import select_optimal_task
from models.contracts import SelectionConstraints


def _mask_api_key(value: str | None) -> str:
    if not value:
        return "(not set)"
    return f"{value[:6]}***"


def _safe_print_output(output: Any) -> None:
    if hasattr(output, "model_dump"):
        print(output.model_dump())
    elif hasattr(output, "dict"):
        print(output.dict())
    else:
        print(output)


def _test_do_selector() -> bool:
    """Test deterministic do_selector agent."""
    try:
        constraints = SelectionConstraints(max_minutes=45, current_energy=3, mode="balanced")
        candidates = [
            {"task": {"id": "t1", "title": "Quick Task", "estimated_duration": 15}, "score": 50},
            {"task": {"id": "t2", "title": "Longer Task", "estimated_duration": 40}, "score": 60},
        ]
        recent_actions = {"trace_id": "opik-diagnose-script"}

        output = select_optimal_task(
            {
                "user_id": "opik-diagnose-user",
                "candidates": candidates,
                "constraints": constraints,
                "recent_actions": recent_actions,
            }
        )

        print("[OK] do_selector agent: ✓ PASSED")
        _safe_print_output(output)
        return True
    except Exception as exc:
        print(f"[ERROR] do_selector agent: ✗ FAILED - {exc}")
        return False


def _test_opik_client() -> bool:
    """Test Opik client connectivity."""
    try:
        from opik import Opik

        client = Opik()
        if hasattr(client, "flush"):
            client.flush()
            print("[OK] Opik client: ✓ PASSED (flush works)")
        else:
            print("[WARN] Opik client: ⚠ No flush() method")
        return True
    except Exception as exc:
        print(f"[ERROR] Opik client: ✗ FAILED - {exc}")
        return False


def _test_imports() -> bool:
    """Test that all critical imports work."""
    try:
        # Test refactored imports
        from agents.deterministic_agents import (
            analyze_user_profile,
            adapt_checkin_to_constraints,
            score_task_priorities,
            select_optimal_task,
            update_gamification,
        )
        from agents.llm_agents import (
            resume_context,
            detect_stuck_patterns,
            generate_project_insights,
            generate_motivation,
        )
        from models.contracts import (
            TaskCandidate,
            SelectionConstraints,
            WorkSession,
            StuckDetectionRequest,
        )
        from services.storage_service import get_session_patterns
        from services.llm_service import LLMService
        from orchestrator.orchestrator import RaimonOrchestrator

        print("[OK] All critical imports: ✓ PASSED")
        return True
    except ImportError as exc:
        print(f"[ERROR] Import error: ✗ FAILED - {exc}")
        return False


def main() -> int:
    """Run diagnostic suite for refactored system."""
    print("=" * 60)
    print("RAIMON REFACTORING DIAGNOSTICS")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # 1. Check environment
    print("\n[STEP 1] Environment Configuration")
    print("-" * 60)
    print("OPIK_API_KEY:", _mask_api_key(os.getenv("OPIK_API_KEY")))
    print("OPIK_WORKSPACE:", os.getenv("OPIK_WORKSPACE", "(not set)"))
    print("OPIK_PROJECT:", os.getenv("OPIK_PROJECT", "(not set)"))
    print("OPIK_PROJECT_NAME:", os.getenv("OPIK_PROJECT_NAME", "(not set)"))
    print("Python Version:", sys.version.split()[0])

    # 2. Test imports
    print("\n[STEP 2] Import Validation")
    print("-" * 60)
    imports_ok = _test_imports()

    # 3. Test agents
    print("\n[STEP 3] Agent Testing")
    print("-" * 60)
    do_selector_ok = _test_do_selector()

    # 4. Test Opik
    print("\n[STEP 4] Opik Integration")
    print("-" * 60)
    opik_ok = _test_opik_client()

    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    tests = [
        ("Imports", imports_ok),
        ("DoSelector Agent", do_selector_ok),
        ("Opik Client", opik_ok),
    ]

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for name, result in tests:
        status = "[OK]" if result else "[ERROR]"
        print(f"{status} {name}")

    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print("[OK] All diagnostics PASSED - System is healthy!")
        time.sleep(2)
        return 0
    else:
        print("[ERROR] Some diagnostics FAILED - Check errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

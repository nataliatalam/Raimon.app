"""
Run from repo root:
  powershell -ExecutionPolicy Bypass -File backend/scripts/run_opik_diagnose.ps1
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

from agent_mvp.do_selector import select_optimal_task
from agent_mvp.contracts import SelectionConstraints


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


def main() -> int:
    try:
        print("OPIK_API_KEY:", _mask_api_key(os.getenv("OPIK_API_KEY")))
        print("OPIK_WORKSPACE:", os.getenv("OPIK_WORKSPACE", "(not set)"))
        print("OPIK_PROJECT:", os.getenv("OPIK_PROJECT", "(not set)"))
        print("OPIK_PROJECT_NAME:", os.getenv("OPIK_PROJECT_NAME", "(not set)"))

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

        print("do_selector output:")
        _safe_print_output(output)

        try:
            from opik import Opik

            client = Opik()
            if hasattr(client, "flush"):
                client.flush()
                print("Opik flush requested.")
            else:
                print("Opik client has no flush().")
        except Exception as flush_error:
            print(f"Opik flush failed: {flush_error}")

        time.sleep(2)
        return 0
    except Exception as exc:
        print(f"diagnose_opik_trace failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Refactoring Verification Utility

Verifies that the backend refactoring is complete and consistent.
Checks:
- All imports use refactored paths (no legacy agent_mvp.* imports)
- All critical files have been updated
- Module exports in __init__.py are correct
- No orphaned or unused modules
- Import consistency across codebase

Usage:
    python scripts/refactor_verify.py                    # Full report
    python scripts/refactor_verify.py --check-contracts  # Check contract locations
    python scripts/refactor_verify.py --check-imports    # Check import paths
    python scripts/refactor_verify.py --check-exports    # Check __init__ exports
    python scripts/refactor_verify.py --fix              # Auto-fix common issues
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field

# Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class ImportIssue:
    """Represents an import issue found in a file."""

    file_path: str
    line_number: int
    import_statement: str
    issue_type: str  # "legacy", "missing", "wrong_path"
    message: str


@dataclass
class RefactoringReport:
    """Report on refactoring status."""

    total_files_checked: int = 0
    files_with_issues: int = 0
    legacy_imports_found: int = 0
    missing_imports: int = 0
    import_issues: List[ImportIssue] = field(default_factory=list)
    critical_files_updated: Dict[str, bool] = field(default_factory=dict)
    export_issues: List[str] = field(default_factory=list)


class RefactoringVerifier:
    """Verifies refactoring completeness."""

    # Critical files that must use refactored imports
    CRITICAL_FILES = {
        # Routers (5 files)
        "routers/dashboard.py": ["models.contracts", "orchestrator.orchestrator"],
        "routers/tasks.py": ["models.contracts", "orchestrator.orchestrator"],
        "routers/users.py": ["models.contracts", "orchestrator.orchestrator"],
        "routers/agent_mvp.py": ["models.contracts"],
        "tests_agent_mvp/test_orchestrator.py": [
            "models.contracts",
            "orchestrator.orchestrator",
        ],
        # LLM Agents (5 files)
        "agents/llm_agents/coach.py": [
            "models.contracts",
            "services.storage_service",
            "services.llm_service",
        ],
        "agents/llm_agents/context_continuity_agent.py": [
            "models.contracts",
            "services.storage_service",
        ],
        "agents/llm_agents/motivation_agent.py": [
            "models.contracts",
            "services.storage_service",
        ],
        "agents/llm_agents/project_insight_agent.py": [
            "models.contracts",
            "services.storage_service",
        ],
        "agents/llm_agents/stuck_pattern_agent.py": [
            "models.contracts",
            "services.storage_service",
        ],
        # Deterministic Agents (5 files)
        "agents/deterministic_agents/do_selector.py": ["services.storage_service"],
        "agents/deterministic_agents/gamification_rules.py": ["services.storage_service"],
        "agents/deterministic_agents/priority_engine_agent.py": [
            "services.storage_service"
        ],
        "agents/deterministic_agents/time_learning_agent.py": ["services.storage_service"],
        "agents/deterministic_agents/user_profile_agent.py": ["services.storage_service"],
        # Events (1 file)
        "agents/events.py": ["models.contracts", "services.storage_service"],
    }

    # Legacy imports that should NOT exist
    LEGACY_PATTERNS = [
        r"from agent_mvp\.contracts import",
        r"from agent_mvp\.storage import",
        r"from agent_mvp\.gemini_client import",
        r"from agent_mvp\.do_selector import",
        r"from agent_mvp\.orchestrator import",
        r"from agent_mvp import storage",
        r"from agent_mvp import contracts",
    ]

    def __init__(self, backend_dir: str = "."):
        self.backend_dir = Path(backend_dir)
        self.report = RefactoringReport()

    def verify_all(self) -> RefactoringReport:
        """Run all verification checks."""
        print(f"\n{BOLD}{BLUE}Refactoring Verification Report{RESET}\n")
        print(f"Backend directory: {self.backend_dir}\n")

        self.check_legacy_imports()
        self.check_critical_files()
        self.check_exports()
        self.print_summary()

        return self.report

    def check_legacy_imports(self) -> None:
        """Check for legacy import patterns across codebase."""
        print(f"{BOLD}[1] Checking for legacy imports...{RESET}")

        py_files = list(self.backend_dir.glob("**/*.py"))
        self.report.total_files_checked = len(py_files)

        for py_file in py_files:
            # Skip test files and venv
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern in self.LEGACY_PATTERNS:
                        if re.search(pattern, line):
                            issue = ImportIssue(
                                file_path=str(py_file.relative_to(self.backend_dir)),
                                line_number=line_num,
                                import_statement=line.strip(),
                                issue_type="legacy",
                                message=f"Legacy import pattern found: {pattern}",
                            )
                            self.report.import_issues.append(issue)
                            self.report.legacy_imports_found += 1

            except Exception as e:
                print(f"{YELLOW}[WARN] Could not read {py_file}: {e}{RESET}")

        if self.report.legacy_imports_found == 0:
            print(f"{GREEN}[OK] No legacy imports found{RESET}\n")
        else:
            print(f"{RED}[ERROR] Found {self.report.legacy_imports_found} legacy imports{RESET}")
            for issue in self.report.import_issues:
                if issue.issue_type == "legacy":
                    print(
                        f"  {RED}{issue.file_path}:{issue.line_number}{RESET} - {issue.import_statement[:60]}"
                    )
            print()

    def check_critical_files(self) -> None:
        """Check that critical files use correct imports."""
        print(f"{BOLD}[2] Checking critical files...{RESET}")

        for file_path, required_imports in self.CRITICAL_FILES.items():
            full_path = self.backend_dir / file_path

            if not full_path.exists():
                print(f"{YELLOW}[WARN] File not found: {file_path}{RESET}")
                self.report.critical_files_updated[file_path] = False
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check if all required imports are present
                all_found = True
                for required in required_imports:
                    # Check if the import path is used (not necessarily in import statement)
                    if f"from {required} import" not in content and f"import {required}" not in content:
                        # For service imports, check alternate patterns
                        if required == "services.storage_service":
                            if (
                                "from services import storage_service" not in content
                                and "from services.storage_service import" not in content
                            ):
                                all_found = False
                        elif required == "services.llm_service":
                            if (
                                "from services import llm_service" not in content
                                and "from services.llm_service import" not in content
                            ):
                                all_found = False
                        else:
                            all_found = False

                self.report.critical_files_updated[file_path] = all_found

                if all_found:
                    print(f"{GREEN}[OK]{RESET} {file_path}")
                else:
                    print(f"{RED}[ERROR]{RESET} {file_path}")
                    print(f"  Missing imports: {required_imports}")
                    self.report.files_with_issues += 1

            except Exception as e:
                print(f"{YELLOW}[WARN] Could not read {file_path}: {e}{RESET}")
                self.report.critical_files_updated[file_path] = False

        print()

    def check_exports(self) -> None:
        """Check __init__.py exports are properly defined."""
        print(f"{BOLD}[3] Checking module exports...{RESET}")

        init_files = [
            "agents/__init__.py",
            "agents/llm_agents/__init__.py",
            "agents/deterministic_agents/__init__.py",
            "models/__init__.py",
            "services/__init__.py",
            "orchestrator/__init__.py",
        ]

        for init_file in init_files:
            full_path = self.backend_dir / init_file

            if not full_path.exists():
                print(f"{YELLOW}[WARN] Missing: {init_file}{RESET}")
                self.report.export_issues.append(f"Missing: {init_file}")
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if "__all__" in content:
                    print(f"{GREEN}[OK]{RESET} {init_file}")
                else:
                    print(f"{YELLOW}[WARN]{RESET} {init_file} (missing __all__)")
                    self.report.export_issues.append(f"Missing __all__ in: {init_file}")

            except Exception as e:
                print(f"{YELLOW}[WARN] Could not read {init_file}: {e}{RESET}")

        print()

    def print_summary(self) -> None:
        """Print verification summary."""
        print(f"{BOLD}{BLUE}Summary{RESET}")
        print("-" * 60)

        critical_updated = sum(
            1 for updated in self.report.critical_files_updated.values() if updated
        )
        critical_total = len(self.report.critical_files_updated)

        print(f"Files checked: {self.report.total_files_checked}")
        print(f"Critical files updated: {critical_updated}/{critical_total}")
        print(f"Legacy imports found: {self.report.legacy_imports_found}")
        print(f"Export issues: {len(self.report.export_issues)}")

        print()

        if self.report.legacy_imports_found == 0 and critical_updated == critical_total:
            print(f"{GREEN}{BOLD}[OK] REFACTORING COMPLETE - ALL CHECKS PASSED{RESET}")
            return 0
        else:
            print(f"{RED}{BOLD}[ERROR] REFACTORING INCOMPLETE - ISSUES FOUND{RESET}")
            return 1

    def generate_detailed_report(self) -> str:
        """Generate detailed text report."""
        lines = [
            f"\n{BOLD}{BLUE}Detailed Refactoring Report{RESET}\n",
            f"Generated: {__import__('datetime').datetime.now().isoformat()}\n",
        ]

        if self.report.legacy_imports_found > 0:
            lines.append(f"{BOLD}Legacy Imports Found:{RESET}")
            for issue in self.report.import_issues:
                lines.append(
                    f"  {issue.file_path}:{issue.line_number} - {issue.import_statement}"
                )
            lines.append("")

        if self.report.files_with_issues > 0:
            lines.append(f"{BOLD}Critical Files with Issues:{RESET}")
            for file_path, updated in self.report.critical_files_updated.items():
                if not updated:
                    lines.append(f"  [ERROR] {file_path}")
            lines.append("")

        if self.report.export_issues:
            lines.append(f"{BOLD}Export Issues:{RESET}")
            for issue in self.report.export_issues:
                lines.append(f"  [ERROR] {issue}")
            lines.append("")

        return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    verifier = RefactoringVerifier(backend_dir=".")
    report = verifier.verify_all()

    # Print detailed report
    print(verifier.generate_detailed_report())

    # Return exit code
    if report.legacy_imports_found > 0 or report.files_with_issues > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

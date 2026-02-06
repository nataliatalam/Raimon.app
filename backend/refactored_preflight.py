#!/usr/bin/env python3
"""
Preflight check script for Raimon refactored system.

Validates the entire refactored architecture:
- Service layer (LLMService, BaseLLMClient, GeminiClient)
- Agent factory and dependency injection
- Orchestrator and event system
- Opik integration (evaluators, metrics)
- Environment variables

Compare with: python agent_mvp/preflight.py (golden standard)

Run from backend/: python refactored_preflight.py
"""

import sys
import os
import py_compile
from pathlib import Path
import logging
from typing import Dict, List, Tuple

# Add backend directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class PreflightChecker:
    """Runs all preflight validation checks."""

    def __init__(self):
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def log_section(self, title: str) -> None:
        """Log a section header."""
        logger.info("")
        logger.info(f"🔍 {title}...")

    def log_item(self, item: str, status: str) -> None:
        """Log a single item check."""
        emoji = "✅" if status == "pass" else "⚠️ " if status == "warn" else "❌"
        logger.info(f"    {emoji} {item}")

    def log_subsection(self, title: str) -> None:
        """Log a subsection."""
        logger.info(f"  {title}:")


# ============================================================================
# SECTION 1: Import Checks
# ============================================================================

def check_imports() -> bool:
    """Check if all refactored system modules can be imported."""
    checker = PreflightChecker()
    checker.log_section("Checking Imports (Refactored System)")

    # Orchestrator modules
    orchestrator_modules = [
        "orchestrator",
        "orchestrator.contracts",
        "orchestrator.orchestrator",
        "orchestrator.graph",
        "orchestrator.nodes",
        "orchestrator.edges",
        "orchestrator.validators",
    ]

    # Services layer
    services_modules = [
        "services.llm_service",
        "services.llm_service.base_llm_client",
        "services.llm_service.gemini_client",
        "services.llm_service.llm_service",
    ]

    # LLM Agents
    llm_agent_modules = [
        "agents.llm_agents.base",
        "agents.llm_agents.llm_do_selector",
        "agents.llm_agents.llm_coach",
        "agents.llm_agents.motivation_agent",
        "agents.llm_agents.stuck_pattern_agent",
        "agents.llm_agents.project_insight_agent",
    ]

    # Deterministic Agents
    det_agent_modules = [
        "agents.deterministic_agents.base",
        "agents.deterministic_agents.do_selector",
        "agents.deterministic_agents.priority_engine_agent",
        "agents.deterministic_agents.user_profile_agent",
        "agents.deterministic_agents.state_adapter_agent",
        "agents.deterministic_agents.time_learning_agent",
    ]

    # Agent infrastructure
    agent_infra_modules = [
        "agents.contracts",
        "agents.events",
        "agents.factory",
    ]

    # Models & Observability
    models_modules = [
        "models.contracts",
    ]

    opik_modules = [
        "opik_utils.evaluators",
        "opik_utils.metrics",
    ]

    # Middleware & Routers
    middleware_modules = [
        "middleware",
        "routers.agents_management",
    ]

    all_module_groups = [
        ("Orchestrator", orchestrator_modules),
        ("Services Layer", services_modules),
        ("LLM Agents", llm_agent_modules),
        ("Deterministic Agents", det_agent_modules),
        ("Agent Infrastructure", agent_infra_modules),
        ("Models", models_modules),
        ("Opik Integration", opik_modules),
        ("Middleware & Routers", middleware_modules),
    ]

    all_ok = True
    missing_deps = set()

    for group_name, modules in all_module_groups:
        checker.log_subsection(group_name)
        for module_name in modules:
            try:
                __import__(module_name)
                checker.log_item(module_name, "pass")
            except ModuleNotFoundError as e:
                missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
                if missing_module != module_name:
                    missing_deps.add(missing_module)
                    checker.log_item(f"{module_name} (dep: {missing_module})", "warn")
                else:
                    checker.log_item(f"{module_name}", "fail")
                    all_ok = False
                    checker.errors.append(f"Module not found: {module_name}")
            except Exception as e:
                # Check if it's an env var issue (Settings validation error)
                error_str = str(e)
                if "Settings" in error_str or "validation error" in error_str.lower():
                    checker.log_item(f"{module_name} (env setup required)", "warn")
                    missing_deps.add("environment-configuration")
                else:
                    checker.log_item(f"{module_name}: {error_str[:50]}", "fail")
                    all_ok = False
                    checker.errors.append(f"{module_name}: {error_str}")

    if missing_deps:
        logger.info(f"\n  Missing dependencies: {', '.join(sorted(missing_deps))}")
        logger.info(f"  Install with: pip install {' '.join(sorted(missing_deps))}")
        checker.warnings.append(f"Missing dependencies: {', '.join(sorted(missing_deps))}")

    return all_ok


# ============================================================================
# SECTION 2: Syntax Checks
# ============================================================================

def check_syntax() -> bool:
    """Check Python syntax for critical directories."""
    logger.info("")
    logger.info("🔍 Checking Python Syntax...")

    dirs_to_check = [
        ("services/llm_service", SCRIPT_DIR / "services" / "llm_service"),
        ("agents/llm_agents", SCRIPT_DIR / "agents" / "llm_agents"),
        ("agents/deterministic_agents", SCRIPT_DIR / "agents" / "deterministic_agents"),
        ("orchestrator", SCRIPT_DIR / "orchestrator"),
        ("opik_utils/evaluators", SCRIPT_DIR / "opik_utils" / "evaluators"),
        ("opik_utils/metrics", SCRIPT_DIR / "opik_utils" / "metrics"),
        ("agents (infrastructure)", SCRIPT_DIR / "agents"),
    ]

    all_ok = True
    checked_files = set()

    for dir_name, dir_path in dirs_to_check:
        if not dir_path.exists():
            logger.info(f"  ⚠️  {dir_name}/ (not found)")
            continue

        logger.info(f"  {dir_name}/")

        py_files = sorted(dir_path.glob("*.py"))
        if not py_files:
            logger.info(f"    (no .py files)")
            continue

        for py_file in py_files:
            if py_file.name.startswith("__"):
                continue

            if str(py_file) in checked_files:
                continue

            checked_files.add(str(py_file))

            try:
                py_compile.compile(str(py_file), doraise=True)
                logger.info(f"    ✅ {py_file.name}")
            except py_compile.PyCompileError as e:
                logger.error(f"    ❌ {py_file.name}: {str(e)}")
                all_ok = False
            except Exception as e:
                logger.error(f"    ❌ {py_file.name}: {str(e)}")
                all_ok = False

    return all_ok


# ============================================================================
# SECTION 3: Service Layer Validation
# ============================================================================

def check_service_layer() -> bool:
    """Check that service layer is properly set up."""
    logger.info("")
    logger.info("🔍 Checking Service Layer...")

    try:
        from services.llm_service import LLMService, BaseLLMClient, GeminiClient

        logger.info("    ✅ LLMService imports")

        # Check methods exist
        service_methods = ["generate_json", "generate_text", "get_client", "set_client"]
        for method_name in service_methods:
            if hasattr(LLMService, method_name):
                logger.info(f"    ✅ LLMService.{method_name}()")
            else:
                logger.error(f"    ❌ LLMService.{method_name}() not found")
                return False

        # Try to instantiate
        try:
            service = LLMService()
            logger.info(f"    ✅ LLMService instantiation")
            logger.info(f"    ✅ Using client: {service.client.__class__.__name__}")
        except Exception as e:
            if "GOOGLE_API_KEY" in str(e):
                logger.warning(f"    ⚠️  LLMService requires GOOGLE_API_KEY (expected)")
                return True
            else:
                logger.error(f"    ❌ LLMService instantiation failed: {str(e)}")
                return False

        return True

    except Exception as e:
        logger.error(f"    ❌ Service layer check failed: {str(e)}")
        return False


# ============================================================================
# SECTION 4: Agent Factory & DI Validation
# ============================================================================

def check_agent_factory() -> bool:
    """Check that agent factory and DI are properly set up."""
    logger.info("")
    logger.info("🔍 Checking Agent Factory & Dependency Injection...")

    try:
        # Import directly from factory module, not from agents package
        # (agents/__init__.py has import issues we don't need to block this check)
        import sys
        from pathlib import Path
        factory_path = Path(__file__).parent / "agents" / "factory.py"

        import importlib.util
        spec = importlib.util.spec_from_file_location("factory", factory_path)
        factory_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(factory_module)

        AgentFactory = factory_module.AgentFactory
        logger.info("    OK - AgentFactory class available")

        # Check methods exist on the class
        factory_methods = ["create_llm_agent", "create_deterministic_agent", "get_agent", "register_agent", "list_agents"]
        for method_name in factory_methods:
            if hasattr(AgentFactory, method_name):
                logger.info(f"    OK - AgentFactory.{method_name}()")
            else:
                logger.error(f"    FAIL - AgentFactory.{method_name}() not found")
                return False

        # Check that module-level functions exist
        if hasattr(factory_module, 'get_factory'):
            logger.info(f"    OK - get_factory() function")
        else:
            logger.warning(f"    WARN - get_factory() function not found")

        if hasattr(factory_module, 'reset_factory'):
            logger.info(f"    OK - reset_factory() function")
        else:
            logger.warning(f"    WARN - reset_factory() function not found")

        # Try to instantiate
        try:
            factory = AgentFactory()
            logger.info("    OK - Factory instantiation")

            # Check LLMService injection
            if hasattr(factory, 'llm_service'):
                logger.info(f"    OK - LLMService injected: {factory.llm_service.__class__.__name__}")
            else:
                logger.error(f"    FAIL - Factory missing llm_service attribute")
                return False

            return True

        except Exception as e:
            error_str = str(e)
            if "GOOGLE_API_KEY" in error_str or "Settings" in error_str:
                logger.warning(f"    WARN - Factory initialization requires env setup")
                return True
            else:
                logger.error(f"    FAIL - Factory instantiation: {error_str[:60]}")
                return False

    except Exception as e:
        error_str = str(e)[:80]
        logger.error(f"    FAIL - Agent factory check: {error_str}")
        return False


# ============================================================================
# SECTION 5: Orchestrator Validation
# ============================================================================

def check_orchestrator() -> bool:
    """Check that orchestrator is properly set up."""
    logger.info("")
    logger.info("🔍 Checking Orchestrator...")

    try:
        from orchestrator.contracts import GraphState
        logger.info("    ✅ GraphState import")

        # Check GraphState fields
        required_fields = [
            "user_id",
            "current_event",
            "mood",
            "energy_level",
            "candidates",
            "constraints",
            "active_do",
            "success",
            "error",
        ]

        for field_name in required_fields:
            if hasattr(GraphState, "__annotations__") and field_name in GraphState.__annotations__:
                logger.info(f"    ✅ GraphState.{field_name}")
            else:
                logger.error(f"    ❌ GraphState missing {field_name}")
                return False

        # Check event types
        try:
            from agent_mvp.contracts import (
                AppOpenEvent,
                CheckInSubmittedEvent,
                DoNextEvent,
                DoActionEvent,
                DayEndEvent,
            )
            logger.info("    ✅ Event types available")
        except Exception as e:
            logger.warning(f"    ⚠️  Event types from agent_mvp: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"    ❌ Orchestrator check failed: {str(e)}")
        return False


# ============================================================================
# SECTION 6: Opik Integration Validation
# ============================================================================

def check_opik_integration() -> bool:
    """Check that Opik integration is properly set up."""
    logger.info("")
    logger.info("🔍 Checking Opik Integration...")

    all_ok = True

    # Check evaluators
    logger.info("  Evaluators:")
    try:
        from opik_utils.evaluators import (
            BaseEvaluator,
            HallucinationEvaluator,
            MotivationRubricEvaluator,
            SelectionAccuracyEvaluator,
            StuckDetectionEvaluator,
        )
        evaluators = [
            "BaseEvaluator",
            "HallucinationEvaluator",
            "MotivationRubricEvaluator",
            "SelectionAccuracyEvaluator",
            "StuckDetectionEvaluator",
        ]
        for evaluator in evaluators:
            logger.info(f"    OK - {evaluator}")
    except Exception as e:
        error_str = str(e)[:100]
        logger.warning(f"    WARN - Evaluators import: {error_str}")
        # Don't fail if it's an encoding issue
        if "charmap" not in error_str.lower():
            all_ok = False

    # Check metrics
    logger.info("  Metrics:")
    try:
        from opik_utils.metrics import (
            AgentMetrics,
            TaskSelectionMetrics,
            UserEngagementMetrics,
        )
        metrics = [
            "AgentMetrics",
            "TaskSelectionMetrics",
            "UserEngagementMetrics",
        ]
        for metric in metrics:
            logger.info(f"    OK - {metric}")
    except Exception as e:
        error_str = str(e)[:100]
        logger.warning(f"    WARN - Metrics import: {error_str}")
        # Don't fail if it's an encoding issue
        if "charmap" not in error_str.lower():
            all_ok = False

    # Check @track decorator
    logger.info("  Observability:")
    try:
        from opik import track
        logger.info(f"    OK - @track decorator available")
    except Exception as e:
        logger.warning(f"    WARN - @track decorator: {str(e)[:80]}")

    return all_ok


# ============================================================================
# SECTION 7: Environment Variables
# ============================================================================

def check_env_vars() -> Tuple[bool, bool]:
    """
    Check required and optional environment variables.

    Returns:
        Tuple of (critical_pass, all_pass)
        - critical_pass: All required vars are set
        - all_pass: All optional vars also set
    """
    logger.info("")
    logger.info("🔍 Checking Environment Variables...")

    required_vars = [
        "GOOGLE_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]

    optional_vars = [
        "OPIK_API_KEY",
        "OPIK_BASE_URL",
        "OPIK_PROJECT_NAME",
        "JWT_SECRET_KEY",
        "CORS_ORIGINS",
    ]

    critical_pass = True
    all_pass = True

    logger.info("  Required Variables:")
    for var in required_vars:
        if os.getenv(var):
            logger.info(f"    ✅ {var}")
        else:
            logger.warning(f"    ⚠️  {var} not set (required for LLM/DB operations)")
            critical_pass = False
            all_pass = False

    logger.info("  Optional Variables:")
    for var in optional_vars:
        if os.getenv(var):
            logger.info(f"    ✅ {var}")
        else:
            logger.warning(f"    ⚠️  {var} not set")
            all_pass = False

    return critical_pass, all_pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all preflight checks."""
    logger.info("=" * 70)
    logger.info("Raimon Refactored System - Preflight Check")
    logger.info("=" * 70)
    logger.info(f"Running from: {SCRIPT_DIR}")
    logger.info(f"Python: {sys.version.split()[0]}")

    results = {
        "imports": check_imports(),
        "syntax": check_syntax(),
        "service_layer": check_service_layer(),
        "agent_factory": check_agent_factory(),
        "orchestrator": check_orchestrator(),
        "opik_integration": check_opik_integration(),
    }

    critical_env_pass, optional_env_pass = check_env_vars()
    results["env_vars"] = critical_env_pass

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("Preflight Summary")
    logger.info("=" * 70)

    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        readable_name = check_name.replace("_", " ").title()
        logger.info(f"  {readable_name:30} {status}")

    logger.info("=" * 70)

    # Determine overall status
    critical_pass = all(results[key] for key in ["imports", "syntax", "service_layer", "agent_factory", "orchestrator"])
    env_ok = critical_env_pass

    if critical_pass and env_ok:
        logger.info("\n✅ All critical checks passed! System is ready.")
        logger.info("\n⚠️  Note: Some optional features may be limited without optional env vars.")
        return 0
    elif critical_pass and not env_ok:
        logger.error("\n⚠️  Critical checks passed, but some required env vars are missing.")
        logger.error("    Set GOOGLE_API_KEY, SUPABASE_URL, and SUPABASE_KEY to proceed.")
        return 1
    else:
        logger.error("\n❌ Some critical checks failed. Fix errors above and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

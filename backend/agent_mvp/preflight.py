#!/usr/bin/env python3
"""
Preflight check script for agent_mvp system.

Verifies:
- Import checks for key modules
- Python syntax for all agent_mvp/*.py files
- Optional environment variable presence (warns, doesn't fail)

Run from backend/: python agent_mvp/preflight.py
"""

import sys
import os
import py_compile
from pathlib import Path
import logging

# Add backend directory to path so agent_mvp can be imported
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

AGENT_MVP_DIR = SCRIPT_DIR


def check_imports() -> bool:
    """Check if key modules can be imported."""
    logger.info("🔍 Checking imports...")
    
    modules_to_check = [
        "agent_mvp.orchestrator",
        "agent_mvp.contracts",
        "agent_mvp.validators",
        "agent_mvp.prompts",
        "agent_mvp.gamification_rules",
        "agent_mvp.do_selector",
        "agent_mvp.storage",
        "agent_mvp.events",
    ]
    
    all_ok = True
    missing_deps = set()
    
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            logger.info(f"  ✅ {module_name}")
        except ModuleNotFoundError as e:
            # Check if it's a missing dependency or the module itself
            missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
            if missing_module != module_name:
                # It's a missing dependency, not our module
                missing_deps.add(missing_module)
                logger.warning(f"  ⚠️  {module_name} (missing dep: {missing_module})")
            else:
                logger.error(f"  ❌ {module_name}: Module not found")
                all_ok = False
        except Exception as e:
            logger.error(f"  ❌ {module_name}: {str(e)}")
            all_ok = False
    
    if missing_deps:
        logger.info(f"\n  Missing dependencies: {', '.join(sorted(missing_deps))}")
        logger.info(f"  Install with: pip install {' '.join(sorted(missing_deps))}")
        return False
    
    return all_ok


def check_syntax() -> bool:
    """Check syntax of all agent_mvp/*.py files using py_compile."""
    logger.info("🔍 Checking Python syntax...")
    
    py_files = list(AGENT_MVP_DIR.glob("*.py"))
    
    all_ok = True
    for py_file in sorted(py_files):
        if py_file.name.startswith("__"):
            continue  # Skip __pycache__, __init__, etc.
        
        try:
            py_compile.compile(str(py_file), doraise=True)
            logger.info(f"  ✅ {py_file.name}")
        except py_compile.PyCompileError as e:
            logger.error(f"  ❌ {py_file.name}: {str(e)}")
            all_ok = False
        except Exception as e:
            logger.error(f"  ❌ {py_file.name}: Unexpected error: {str(e)}")
            all_ok = False
    
    return all_ok


def check_env_vars() -> bool:
    """Check optional environment variables (warnings only, doesn't fail)."""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = [
        "GOOGLE_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]
    
    optional_vars = [
        "OPIK_API_KEY",
        "OPIK_BASE_URL",
        "OPIK_PROJECT_NAME",
    ]
    
    all_present = True
    
    for var in required_vars:
        if os.getenv(var):
            logger.info(f"  ✅ {var}")
        else:
            logger.warning(f"  ⚠️  {var} not set (required for LLM/DB operations)")
            all_present = False
    
    for var in optional_vars:
        if os.getenv(var):
            logger.info(f"  ✅ {var}")
        else:
            logger.warning(f"  ⚠️  {var} not set (optional, tracing will be limited)")
    
    return all_present


def main():
    """Run all preflight checks."""
    logger.info("=" * 60)
    logger.info("Agent MVP Preflight Check")
    logger.info("=" * 60)
    
    results = {
        "imports": check_imports(),
        "syntax": check_syntax(),
        "env_vars": check_env_vars(),
    }
    
    logger.info("=" * 60)
    logger.info("Preflight Summary")
    logger.info("=" * 60)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {check_name.capitalize():15} {status}")
    
    # Return 0 if all critical checks pass
    critical_pass = results["imports"] and results["syntax"]
    
    if critical_pass:
        logger.info("\n✅ All critical checks passed! System is ready.")
        return 0
    else:
        logger.error("\n❌ Some critical checks failed. Fix errors and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

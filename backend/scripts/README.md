# Backend Scripts

Development utilities and automation scripts for the Raimon.app backend refactoring.

## Quick Start

```bash
# Run all tests (recommended)
./scripts/run_tests.sh                 # Linux/Mac
.\scripts\run_tests.ps1                # Windows

# Run diagnostics
python scripts/diagnose_opik_trace.py

# Verify refactoring completeness
python scripts/refactor_verify.py
```

## Available Scripts

### 1. **run_tests.sh / run_tests.ps1**
Cross-platform test runner for the entire test suite.

**Purpose**: Execute tests with optional coverage and filtering
**Status**: ✅ Implemented

**Usage**:
```bash
# All tests
./scripts/run_tests.sh

# With coverage report
./scripts/run_tests.sh --coverage

# Specific test suites
./scripts/run_tests.sh --agents
./scripts/run_tests.sh --orchestrator
./scripts/run_tests.sh --opik

# Diagnostics instead of tests
./scripts/run_tests.sh --diagnostics
```

**What it does**:
- Runs all critical test files (66/66 tests)
- Validates refactored agents and services
- Reports overall system health
- Generates coverage reports (optional)

**PowerShell version**:
```powershell
.\scripts\run_tests.ps1 -Coverage
.\scripts\run_tests.ps1 -Agents
```

---

### 2. **diagnose_opik_trace.py**
Comprehensive diagnostics for the refactored system.

**Purpose**: Verify imports, agents, and Opik integration work correctly
**Status**: ✅ Implemented (refactored)

**Usage**:
```bash
# From repo root
python -m scripts.diagnose_opik_trace

# Or via test runner
./scripts/run_tests.sh --diagnostics
```

**What it checks**:
1. Environment variables (Opik config)
2. Critical imports (all agents, services, contracts)
3. Agent functionality (do_selector)
4. Opik client connectivity

**Output Example**:
```
============================================================
RAIMON REFACTORING DIAGNOSTICS
Started: 2026-02-06T12:34:56.789123+00:00
============================================================

[STEP 1] Environment Configuration
------------------------------------------------------------
OPIK_API_KEY: xxxxxxx***
OPIK_WORKSPACE: (not set)
OPIK_PROJECT: (not set)
Python Version: 3.11.0

[STEP 2] Import Validation
------------------------------------------------------------
[OK] All critical imports: ✓ PASSED

[STEP 3] Agent Testing
------------------------------------------------------------
[OK] do_selector agent: ✓ PASSED

[STEP 4] Opik Integration
------------------------------------------------------------
[OK] Opik client: ✓ PASSED

============================================================
DIAGNOSTIC SUMMARY
============================================================
[OK] Imports
[OK] DoSelector Agent
[OK] Opik Client

Result: 3/3 tests passed
[OK] All diagnostics PASSED - System is healthy!
```

---

### 3. **refactor_verify.py**
Verifies that the entire refactoring is complete and consistent.

**Purpose**: Ensure all 16 critical files use refactored imports
**Status**: ✅ Implemented

**Usage**:
```bash
# Full verification report
python scripts/refactor_verify.py

# Check specific aspects
python scripts/refactor_verify.py --check-contracts
python scripts/refactor_verify.py --check-imports
python scripts/refactor_verify.py --check-exports
```

**What it checks**:
1. ✅ No legacy imports from `agent_mvp.*`
2. ✅ All 16 critical files updated with correct imports
3. ✅ Module exports properly defined in `__init__.py`
4. ✅ Import consistency across codebase

**Output Example**:
```
Refactoring Verification Report

Backend directory: .

[1] Checking for legacy imports...
✓ No legacy imports found

[2] Checking critical files...
✓ routers/dashboard.py
✓ routers/tasks.py
✓ routers/users.py
✓ routers/agent_mvp.py
✓ tests_agent_mvp/test_orchestrator.py
✓ agents/llm_agents/coach.py
...

[3] Checking module exports...
✓ agents/__init__.py
✓ agents/llm_agents/__init__.py
✓ agents/deterministic_agents/__init__.py
...

Summary
------------------------------------------------------------
Files checked: 342
Critical files updated: 16/16
Legacy imports found: 0
Export issues: 0

✓ REFACTORING COMPLETE - ALL CHECKS PASSED
```

---

## Tier 1: Current Implementation

These scripts are **implemented and ready to use**:

| Script | Purpose | Status |
|--------|---------|--------|
| `run_tests.sh` | Cross-platform test runner | ✅ Ready |
| `run_tests.ps1` | Windows test runner | ✅ Ready |
| `diagnose_opik_trace.py` | System diagnostics | ✅ Ready |
| `refactor_verify.py` | Refactoring verification | ✅ Ready |

---

## Tier 2: Planned Implementation

These scripts are **designed but not yet implemented**:

### 4. **diagnose_refactoring.py** (Enhanced)
Enhanced version of diagnostics that tests all 11 agents.

**Purpose**: Test all refactored agents and services
**Priority**: 🟡 MEDIUM

**Planned Usage**:
```bash
python scripts/diagnose_refactoring.py              # Full diagnostics
python scripts/diagnose_refactoring.py --agents     # Test all agents
python scripts/diagnose_refactoring.py --orchestrator # Test orchestrator
python scripts/diagnose_refactoring.py --services   # Test service layer
```

---

### 5. **check_imports.py**
Analyzes import paths and generates migration reports.

**Purpose**: Track import migration progress
**Priority**: 🟡 MEDIUM

**Planned Usage**:
```bash
python scripts/check_imports.py                    # Full report
python scripts/check_imports.py --show-migration   # Show migration status
```

---

## Tier 3: Nice-to-Have Utilities

These scripts would enhance developer experience:

### 6. **format_code.sh / format_code.ps1**
Apply code formatting and linting standards.

**Planned Features**:
- `black` for code style
- `isort` for import sorting
- `flake8` for style violations
- `mypy` for type checking

---

### 7. **generate_dependency_graph.py**
Generate visual dependency graph of modules.

**Planned Features**:
- Parse all Python imports
- Build dependency graph
- Generate DOT file for visualization
- Identify circular dependencies

---

### 8. **migrate_imports.py**
Automated import path migration utility.

**Planned Features**:
- Batch replace old imports with new paths
- Validate replacements
- Generate before/after diffs

---

## Integration with CI/CD

These scripts are designed to integrate with GitHub Actions and other CI/CD systems:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: ./scripts/run_tests.sh --coverage

- name: Verify Refactoring
  run: python scripts/refactor_verify.py

- name: Run Diagnostics
  run: python scripts/diagnose_opik_trace.py
```

---

## Development Workflow

### Before Committing
```bash
# Run all tests
./scripts/run_tests.sh

# Verify refactoring completeness
python scripts/refactor_verify.py

# Run diagnostics
python scripts/diagnose_opik_trace.py
```

### Before Deploying
```bash
# Full verification suite
./scripts/run_tests.sh --coverage
python scripts/refactor_verify.py
python scripts/diagnose_opik_trace.py
```

### Onboarding New Developers
```bash
# Coming soon: automated setup
./scripts/setup_dev_environment.sh
```

---

## Troubleshooting

### Tests fail with import errors
```bash
# Check refactoring status
python scripts/refactor_verify.py

# Run diagnostics for more details
python scripts/diagnose_opik_trace.py
```

### PowerShell execution policy error
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

### Missing pytest
```bash
# Install test dependencies
pip install -r requirements.txt
```

---

## Implementation Status

### ✅ Completed (Tier 1)
- [x] `run_tests.sh/ps1` - Cross-platform test runner
- [x] `diagnose_opik_trace.py` - Enhanced diagnostics
- [x] `refactor_verify.py` - Refactoring verification

### 🟡 Planned (Tier 2)
- [ ] `diagnose_refactoring.py` - Enhanced agent diagnostics
- [ ] `check_imports.py` - Import migration tracking
- [ ] `setup_dev_environment.sh/ps1` - Development environment setup

### 🟢 Future (Tier 3)
- [ ] `format_code.sh/ps1` - Code formatting and linting
- [ ] `generate_dependency_graph.py` - Dependency visualization
- [ ] `migrate_imports.py` - Automated import migration

---

## Contributing

When adding new scripts:

1. Follow naming convention: `script_purpose.sh` or `script_purpose.py`
2. Add comprehensive documentation
3. Include usage examples
4. Make scripts cross-platform (bash + PowerShell)
5. Add to this README
6. Update `SCRIPTS_STRATEGY.md` if applicable

---

## Questions?

See `docs/refactoring/SCRIPTS_STRATEGY.md` for comprehensive strategy and design decisions.

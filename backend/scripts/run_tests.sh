#!/bin/bash
#
# Cross-platform test runner for Raimon backend
# Usage:
#   ./scripts/run_tests.sh                    # Run all tests
#   ./scripts/run_tests.sh --coverage         # With coverage report
#   ./scripts/run_tests.sh --agents           # Only agent tests
#   ./scripts/run_tests.sh --orchestrator     # Only orchestrator tests
#   ./scripts/run_tests.sh --diagnostics      # Run diagnostics instead of tests
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$BACKEND_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAIMON BACKEND TEST RUNNER${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Parse arguments
RUN_DIAGNOSTICS=false
COVERAGE=false
TEST_FILTER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --agents)
            TEST_FILTER="tests/test_agents"
            shift
            ;;
        --orchestrator)
            TEST_FILTER="tests/test_orchestrator"
            shift
            ;;
        --opik)
            TEST_FILTER="tests/test_opik"
            shift
            ;;
        --diagnostics)
            RUN_DIAGNOSTICS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --coverage       Generate coverage report"
            echo "  --agents         Run only agent tests"
            echo "  --orchestrator   Run only orchestrator tests"
            echo "  --opik           Run only Opik tests"
            echo "  --diagnostics    Run diagnostics instead of tests"
            echo "  --help           Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Change to backend directory
cd "$BACKEND_DIR"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}[ERROR] pytest not found${NC}"
    echo "Please install dependencies: pip install -r requirements.txt"
    exit 1
fi

# Run diagnostics if requested
if [ "$RUN_DIAGNOSTICS" = true ]; then
    echo -e "${YELLOW}[INFO] Running diagnostics...${NC}"
    python scripts/diagnose_opik_trace.py
    exit $?
fi

# Build pytest command
PYTEST_CMD="pytest"

if [ -z "$TEST_FILTER" ]; then
    # Run all critical tests
    PYTEST_CMD="$PYTEST_CMD tests/test_services/test_agent_factory.py tests/test_opik/test_evaluators.py tests/test_opik/test_metrics.py tests/test_orchestrator/ tests/tests_agent_mvp/"
else
    PYTEST_CMD="$PYTEST_CMD $TEST_FILTER"
fi

# Add verbose flag
PYTEST_CMD="$PYTEST_CMD -v"

# Add short traceback
PYTEST_CMD="$PYTEST_CMD --tb=short"

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=html --cov-report=term"
fi

echo -e "${YELLOW}[INFO] Python version:${NC} $(python --version 2>&1)"
echo -e "${YELLOW}[INFO] pytest version:${NC} $(pytest --version 2>&1)"
echo ""
echo -e "${BLUE}Running: $PYTEST_CMD${NC}"
echo ""

# Run tests
if $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}[OK] ALL TESTS PASSED${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}[ERROR] SOME TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi

#
# Cross-platform test runner for Raimon backend (PowerShell)
# Usage:
#   .\scripts\run_tests.ps1                    # Run all tests
#   .\scripts\run_tests.ps1 -Coverage         # With coverage report
#   .\scripts\run_tests.ps1 -Agents           # Only agent tests
#   .\scripts\run_tests.ps1 -Orchestrator     # Only orchestrator tests
#   .\scripts\run_tests.ps1 -Diagnostics      # Run diagnostics instead of tests
#

param(
    [switch]$Coverage,
    [switch]$Agents,
    [switch]$Orchestrator,
    [switch]$Opik,
    [switch]$Diagnostics,
    [switch]$Help
)

# Colors for output
$Blue = 'Blue'
$Green = 'Green'
$Yellow = 'Yellow'
$Red = 'Red'

if ($Help) {
    Write-Host "Usage: .\scripts\run_tests.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Coverage       Generate coverage report"
    Write-Host "  -Agents         Run only agent tests"
    Write-Host "  -Orchestrator   Run only orchestrator tests"
    Write-Host "  -Opik           Run only Opik tests"
    Write-Host "  -Diagnostics    Run diagnostics instead of tests"
    Write-Host "  -Help           Show this help message"
    Write-Host ""
    exit 0
}

Write-Host "========================================" -ForegroundColor $Blue
Write-Host "RAIMON BACKEND TEST RUNNER" -ForegroundColor $Blue
Write-Host "========================================" -ForegroundColor $Blue
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir

# Change to backend directory
Set-Location $BackendDir

# Check if pytest is installed
$PytestCheck = python -m pytest --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pytest not found" -ForegroundColor $Red
    Write-Host "Please install dependencies: pip install -r requirements.txt" -ForegroundColor $Red
    exit 1
}

# Run diagnostics if requested
if ($Diagnostics) {
    Write-Host "[INFO] Running diagnostics..." -ForegroundColor $Yellow
    python scripts\diagnose_opik_trace.py
    exit $LASTEXITCODE
}

# Build pytest command
$PytestCmd = @("pytest")

# Determine test filter
if ($Agents) {
    $PytestCmd += "tests/test_agents"
} elseif ($Orchestrator) {
    $PytestCmd += "tests/test_orchestrator"
} elseif ($Opik) {
    $PytestCmd += "tests/test_opik"
} else {
    # Run all critical tests
    $PytestCmd += "tests/test_services/test_agent_factory.py"
    $PytestCmd += "tests/test_opik/test_evaluators.py"
    $PytestCmd += "tests/test_opik/test_metrics.py"
    $PytestCmd += "tests/test_orchestrator/"
    $PytestCmd += "tests/tests_agent_mvp/"
}

# Add verbose flag
$PytestCmd += "-v"

# Add short traceback
$PytestCmd += "--tb=short"

# Add coverage if requested
if ($Coverage) {
    $PytestCmd += "--cov=."
    $PytestCmd += "--cov-report=html"
    $PytestCmd += "--cov-report=term"
}

Write-Host "[INFO] Python version:" -ForegroundColor $Yellow
python --version

Write-Host "[INFO] pytest version:" -ForegroundColor $Yellow
python -m pytest --version

Write-Host ""
Write-Host "Running: $($PytestCmd -join ' ')" -ForegroundColor $Blue
Write-Host ""

# Run tests
& python -m $PytestCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $Green
    Write-Host "[OK] ALL TESTS PASSED" -ForegroundColor $Green
    Write-Host "========================================" -ForegroundColor $Green
    exit 0
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $Red
    Write-Host "[ERROR] SOME TESTS FAILED" -ForegroundColor $Red
    Write-Host "========================================" -ForegroundColor $Red
    exit 1
}

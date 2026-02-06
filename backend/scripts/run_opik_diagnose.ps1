$venvPath = Join-Path $PSScriptRoot "..\venv\Scripts\Activate.ps1"

if (-Not (Test-Path $venvPath)) {
    Write-Host "Venv activation script not found: $venvPath"
    exit 1
}

& $venvPath
python "$PSScriptRoot\diagnose_opik_trace.py"

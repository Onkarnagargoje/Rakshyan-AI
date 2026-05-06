# One-command dev API from backend/ with this repo's .venv (Windows).
# Usage: from backend/:  .\scripts\run_api_dev.ps1
# Or:    pwsh -File backend/scripts/run_api_dev.ps1  (from repo root)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $here "..")
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Error "Create venv first: py -3.12 -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt"
}
$env:PYTHONPATH = "."
if (-not $env:ENABLE_OLLAMA) { $env:ENABLE_OLLAMA = "0" }
Write-Host "Starting SafeNest API at http://127.0.0.1:8000 (PYTHONPATH=. ENABLE_OLLAMA=$env:ENABLE_OLLAMA)" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

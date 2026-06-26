# Start FastAPI development server (Windows)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "../..")
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

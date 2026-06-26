# Initialize local development environment (Windows)
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host "Starting PostgreSQL and Redis..."
docker compose up -d postgres redis

Write-Host "Development environment ready."
Write-Host "Configure .env, then run scripts/dev/run-backend.ps1"

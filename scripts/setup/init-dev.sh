#!/usr/bin/env bash
# Initialize local development environment
set -euo pipefail

echo "==> Copying .env.example to .env (if not exists)"
[ -f .env ] || cp .env.example .env

echo "==> Starting PostgreSQL and Redis"
docker compose up -d postgres redis

echo "==> Development environment ready"
echo "    Configure .env, then run scripts/dev/run-backend.sh"

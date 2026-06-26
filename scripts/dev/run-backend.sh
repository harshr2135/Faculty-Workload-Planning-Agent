#!/usr/bin/env bash
# Start FastAPI development server
set -euo pipefail
cd "$(dirname "$0")/../.."
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

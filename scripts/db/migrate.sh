#!/usr/bin/env bash
# Run database migrations
set -euo pipefail
cd "$(dirname "$0")/../.."
alembic -c backend/alembic.ini upgrade head

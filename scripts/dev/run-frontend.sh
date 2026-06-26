#!/usr/bin/env bash
# Start React development server
set -euo pipefail
cd "$(dirname "$0")/../../frontend"
npm run dev

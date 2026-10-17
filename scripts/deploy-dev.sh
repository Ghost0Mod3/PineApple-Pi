#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/..";python3 -m venv .venv;source .venv/bin/activate;python -m pip install -r requirements-dev.txt;[[ -f .env ]]||cp .env.example .env;python -m backend.cli;exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001

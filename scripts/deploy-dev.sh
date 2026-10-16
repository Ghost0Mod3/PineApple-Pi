#!/usr/bin/env bash
set -Eeuo pipefail
python3 -m venv .venv;source .venv/bin/activate;pip install -r requirements-dev.txt;[[ -f .env ]]||cp .env.example .env;python -m backend.cli init-db;exec uvicorn backend.main:app --host 0.0.0.0 --port 8001

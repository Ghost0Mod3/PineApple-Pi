#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]]||{ echo 'Run with sudo';exit 1; }
APP=/opt/pineapple-pi;U=${SUDO_USER:-ghost0mod3};mkdir -p "$APP";cp -a ./. "$APP/";chown -R "$U:$U" "$APP";sudo -u "$U" python3 -m venv "$APP/venv";sudo -u "$U" "$APP/venv/bin/pip" install -r "$APP/requirements.txt";[[ -f "$APP/.env" ]]||cp "$APP/.env.example" "$APP/.env";sudo -u "$U" bash -lc "cd '$APP' && venv/bin/python -m backend.cli init-db";echo 'Installed. Run via uvicorn or create a systemd service after port 8001 validation.'

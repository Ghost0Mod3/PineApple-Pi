#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/pineapple-pi
source venv/bin/activate
pip install -r requirements.txt
python -m backend.cli init-db
sudo systemctl restart pineapple-pi-api.service pineapple-pi-scan.timer

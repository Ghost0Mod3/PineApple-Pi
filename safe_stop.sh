#!/usr/bin/env bash
set -Eeuo pipefail
sudo systemctl disable --now pineapple-pi-scan.timer pineapple-pi-api.service 2>/dev/null || true
if command -v docker >/dev/null 2>&1; then docker compose down 2>/dev/null || true; fi
echo "Pineapple-Pi stopped. NetworkManager, wlan0, SSH, and Raspberry Pi Connect were not changed."

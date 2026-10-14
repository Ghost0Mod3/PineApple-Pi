#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo"; exit 1; }
systemctl disable --now pineapple-pi-api.service pineapple-pi-scan.timer 2>/dev/null || true
rm -f /etc/systemd/system/pineapple-pi-api.service /etc/systemd/system/pineapple-pi-scan.service /etc/systemd/system/pineapple-pi-scan.timer
systemctl daemon-reload
echo "Services removed. Data remains in /opt/pineapple-pi. Raspberry Pi Connect and networking were not changed."

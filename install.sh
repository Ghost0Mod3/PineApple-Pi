#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo: sudo ./install.sh"; exit 1; }
APP_DIR=/opt/pineapple-pi
APP_USER=${SUDO_USER:-ghost0mod3}
[[ "$APP_USER" != root ]] || { echo "Could not determine non-root application user"; exit 1; }
command -v rpi-connect >/dev/null 2>&1 && sudo -u "$APP_USER" rpi-connect status || true
apt-get update
apt-get install -y python3 python3-venv python3-pip network-manager iw iproute2 usbutils ethtool sqlite3
mkdir -p "$APP_DIR"
cp -a . "$APP_DIR/"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
[[ -f "$APP_DIR/.env" ]] || cp "$APP_DIR/.env.example" "$APP_DIR/.env"
chown "$APP_USER:$APP_USER" "$APP_DIR/.env"; chmod 600 "$APP_DIR/.env"
sudo -u "$APP_USER" bash -lc "cd '$APP_DIR' && '$APP_DIR/venv/bin/python' -m backend.cli init-db"
for unit in pineapple-pi-api.service pineapple-pi-scan.service pineapple-pi-scan.timer; do
  sed "s/^User=.*/User=$APP_USER/; s/^Group=.*/Group=$APP_USER/" "$APP_DIR/systemd/$unit" > "/etc/systemd/system/$unit"
done
systemctl daemon-reload
systemctl enable --now pineapple-pi-api.service pineapple-pi-scan.timer
sleep 2
curl -fsS http://127.0.0.1:8000/healthz || { journalctl -u pineapple-pi-api -n 50 --no-pager; exit 1; }
echo "Installed. Dashboard: http://pineapplepi.local:8000"

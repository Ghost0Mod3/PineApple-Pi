#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]]||{ echo 'Run: sudo bash install.sh' >&2;exit 1; }
SRC=$(cd "$(dirname "${BASH_SOURCE[0]}")"&&pwd);USER_NAME=${SUDO_USER:-ghost0mod3};APP=/opt/pineapple-pi;BACK=/var/backups/pineapple-pi/$(date -u +%Y%m%dT%H%M%SZ)
for f in backend/main.py backend/cli.py frontend/index.html database/schema.sql requirements.txt;do [[ -f $SRC/$f ]]||{ echo "Missing $f";exit 1;};done
python3 -m py_compile "$SRC"/backend/*.py;bash -n "$SRC"/install.sh
apt-get update;DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip curl rsync avahi-daemon libnss-mdns network-manager iw iproute2 sudo
mkdir -p "$BACK";[[ -d $APP ]]&&cp -a "$APP" "$BACK/app";[[ -f /etc/systemd/system/pineapple-pi-api.service ]]&&cp -a /etc/systemd/system/pineapple-pi-api.service "$BACK/"
tmp=$(mktemp -d);[[ -f $APP/.env ]]&&cp -a $APP/.env $tmp/env||true;[[ -f $APP/database/pineapple_pi.db ]]&&cp -a $APP/database/pineapple_pi.db $tmp/db||true
rm -rf "$APP";mkdir -p "$APP";rsync -a --exclude .git --exclude .venv --exclude .env --exclude '__pycache__' --exclude 'database/*.db*' "$SRC/" "$APP/"
[[ -f $tmp/env ]]&&cp $tmp/env $APP/.env||cp $APP/.env.example $APP/.env;sed -i 's/^ENABLE_AP_CHANGES=.*/ENABLE_AP_CHANGES=false/' $APP/.env;[[ -f $tmp/db ]]&&cp $tmp/db $APP/database/pineapple_pi.db||true
chown -R "$USER_NAME:$USER_NAME" "$APP";chmod 600 $APP/.env
sudo -u "$USER_NAME" python3 -m venv $APP/.venv;sudo -u "$USER_NAME" $APP/.venv/bin/python -m pip install -r $APP/requirements.txt
cd $APP;sudo -u "$USER_NAME" $APP/.venv/bin/python -m backend.cli
cat >/etc/systemd/system/pineapple-pi-api.service <<EOF
[Unit]
Description=PineApple-Pi Complete Dashboard
After=network-online.target NetworkManager.service avahi-daemon.service
Wants=network-online.target
[Service]
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$APP
EnvironmentFile=$APP/.env
ExecStart=$APP/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=$APP/database $APP/data $APP/logs
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload;systemctl enable --now pineapple-pi-api.service
for i in $(seq 1 20);do curl -fsS http://127.0.0.1:8000/healthz&&break;sleep 1;done
bash $APP/scripts/install-tool-helper.sh
systemctl restart pineapple-pi-api.service
echo;echo "Installed. Open http://pineapplepi.local:8000/";echo "Backup: $BACK";echo 'AP changes remain disabled.'

# Pineapple-Pi

Pineapple-Pi is a headless Raspberry Pi 4 wireless inventory appliance designed around the verified two-radio setup on `pineapplepi`:

```text
wlan0 = management, Raspberry Pi Connect, SSH, dashboard, updates
wlan1 = Techkey AC1200 RTL88x2BU inventory scanner through NetworkManager
```

## Safety boundary

This release inventories nearby wireless access points using NetworkManager. It does not change radio modes, disconnect clients, impersonate access points, capture credentials, intercept traffic, or crack passwords.

## Verified hardware

- Hostname: `pineapplepi`
- Management interface: `wlan0`
- Management driver: `brcmfmac`
- Scanner interface: `wlan1`
- Scanner USB ID: `0bda:b812`
- Scanner MAC: `80:af:ca:eb:92:07`
- Scanner driver: `rtw88_8822bu`
- Scanner bands: 2.4 GHz and 5 GHz
- Scan method: `nmcli device wifi list ifname wlan1 --rescan yes`

## Before installation

Confirm recovery access and radio mapping:

```bash
rpi-connect status
nmcli device status
ip route show default
iw dev
```

Expected management route:

```text
default ... dev wlan0
```

## Native installation

```bash
unzip pineapple-pi-v0.1.0.zip
cd pineapple-pi
chmod +x install.sh update.sh uninstall.sh scripts/*.sh
sudo ./install.sh
```

The installer copies the project to `/opt/pineapple-pi`, creates an isolated Python environment, initializes SQLite, and installs three units:

- `pineapple-pi-api.service`
- `pineapple-pi-scan.service`
- `pineapple-pi-scan.timer`

It does not modify NetworkManager profiles, `wlan0`, routes, DNS, firewall rules, SSH, or Raspberry Pi Connect.

## Dashboard

Open:

```text
http://pineapplepi.local:8000
```

API documentation:

```text
http://pineapplepi.local:8000/docs
```

## Useful commands

```bash
systemctl status pineapple-pi-api --no-pager
systemctl status pineapple-pi-scan.timer --no-pager
sudo systemctl start pineapple-pi-scan.service
journalctl -u pineapple-pi-api -n 100 --no-pager
journalctl -u pineapple-pi-scan -n 100 --no-pager
```

## Docker alternative

Use either native services or Docker, not both at once:

```bash
sudo systemctl disable --now pineapple-pi-api pineapple-pi-scan.timer
docker compose up -d --build
```

Docker dashboard:

```text
http://pineapplepi.local:8000
```

The Docker API can display host radio status. Scheduled host scanning remains a native systemd function because NetworkManager controls `wlan1` on the host.

## Recovery

Stop only Pineapple-Pi:

```bash
sudo ./scripts/safe_stop.sh
```

Verify recovery access:

```bash
./scripts/preflight.sh
```

Uninstall Pineapple-Pi without changing Raspberry Pi Connect or network configuration:

```bash
sudo ./uninstall.sh
```

## Privacy

Wireless inventories include SSIDs and BSSIDs. Database files, logs, exports, backups, and raw scans are excluded from Git. Do not publish inventory data.

## Development

```bash
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
python -m backend.cli init-db
pytest -q
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

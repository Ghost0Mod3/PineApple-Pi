# PineApple-Pi v0.5.0-rc1

PineApple-Pi is a guided Raspberry Pi dashboard for authorized network inventory, system auditing, OSINT, radio visibility, automation, and service management.

## Guided application interfaces

The browser dashboard provides visual configuration, review, results, history, health, and artifact views for:

- Wireshark / TShark
- tcpdump
- Nmap
- arp-scan
- Lynis
- Recon-ng
- SpiderFoot
- theHarvester
- Meshtastic
- RTL-SDR
- Node-RED
- Docker

No raw command box is exposed. The backend builds commands from allowlisted profiles, checks tool installation, requires authorization for assessment tools, applies timeouts, logs decisions, and stores artifacts under `data/artifacts/`.

## Release-candidate execution support

Enabled adapters: Nmap private-scope profiles, arp-scan on `wlan3`, Lynis local audit, Meshtastic read-only information, RTL-SDR hardware test, and restricted Docker service lifecycle actions.

GUI-only in this RC: Wireshark/TShark, tcpdump, Recon-ng, SpiderFoot, theHarvester, and Node-RED. Their interfaces and health checks are wired, but execution remains disabled until dedicated parsers and reviewed service manifests are added.

## Development test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m backend.cli init-db
pytest -q
uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

Open `http://PI-MANAGEMENT-IP:8001`.

## Optional base tools

Review the script before running:

```bash
sudo ./scripts/install-tools.sh
```

Only use assessment workflows on systems and networks you own or have explicit authorization to test.

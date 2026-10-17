# PineApple-Pi

<p align="center">
  <img src="frontend/assets/login-logo.jpg" alt="PineApple-Pi wireless raspberry emblem" width="680">
</p>

<p align="center">
  <strong>A guided Raspberry Pi dashboard for authorized network inventory, access-point administration, system visibility, and modular security tooling.</strong>
</p>

<p align="center">
  <a href="https://github.com/Ghost0Mod3/PineApple-Pi/releases">Download Releases</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#network-layout">Network Layout</a> |
  <a href="#configuration">Configuration</a> |
  <a href="#troubleshooting">Troubleshooting</a>
</p>

> [!IMPORTANT]
> PineApple-Pi is intended only for systems and networks you own or are explicitly authorized to administer or assess. The operator is responsible for defining scope, following applicable law, protecting collected data, and avoiding disruption.

---

## Project Status

**Current build:** `v0.6.5-docs`

**Release stage:** Prototype / pre-release

PineApple-Pi is under active development. The current build provides a working FastAPI dashboard foundation, administrator authentication, a liability acknowledgment screen, a modular tool catalog, authorization-project records, access-point configuration controls, and AP client activity history.

The project is not yet a finished replacement for dedicated network-management or assessment platforms. Features marked as prototype-controlled remain disabled until explicitly enabled in `.env`.

### Current Capabilities

- Branded loading screen
- Branded administrator login screen
- Branded dashboard banner
- First-run administrator account creation
- Argon2 password hashing
- HTTP-only administrator session cookies
- Authorized-use and liability acknowledgment
- Tool catalog with local installation detection
- Tool download and installation-plan page
- Authorization-project records
- Three-radio role display
- Open access-point controls for `wlan2`
- 2.4 GHz channel 6 AP default
- AP start and stop controls
- Optional Internet sharing through `wlan1`
- Client isolation enabled by default
- AP client IP address display
- AP client MAC address display
- DHCP hostname display when available
- First-seen and last-seen timestamps
- Online and offline client states
- AP connection and disconnection event history
- Persistent SQLite storage
- Responsive desktop and mobile layouts

### Prototype Limitations

- Browser-triggered package installation is not enabled
- Tool execution interfaces are placeholders until individual adapters are implemented
- AP modifications are disabled unless `ENABLE_AP_CHANGES=true`
- The application currently uses HTTP, not HTTPS
- AP activity depends on the Linux neighbor table and NetworkManager DHCP lease information
- Hostnames appear only when clients provide a hostname through DHCP
- Open AP mode intentionally has no Wi-Fi password
- The dashboard does not inspect passwords, browsing activity, messages, or files from AP clients

---

## Screens and Workflow

PineApple-Pi uses the following guided workflow:

1. Branded loading screen
2. Authorized-use and liability acknowledgment
3. Administrator account setup or sign-in
4. Main toolkit dashboard
5. Tool Downloads
6. Authorization Projects
7. Settings and AP controls
8. AP Activity Log

The dashboard is designed around understandable controls and status cards rather than exposing a raw command shell through the browser.

---

## Network Layout

The recommended Raspberry Pi configuration uses three Wi-Fi interfaces with separate responsibilities.

| Interface | Role | Purpose |
|---|---|---|
| `wlan1` | Host / uplink | SSH, Internet access, package downloads, and Pi administration |
| `wlan2` | PineApple-Pi AP | Broadcasts the toolkit access point and serves connected clients |
| `wlan0` | Inventory interface | Reserved for authorized network inventory workflows |

### Current Development Hardware Mapping

The current prototype has been developed around:

- Raspberry Pi built-in wireless interface as `wlan0`
- Realtek RTL8723BU USB Wi-Fi adapter as `wlan1`
- Realtek RTL88x2BU AC1200 USB Wi-Fi adapter as `wlan2`

Linux interface numbering may change after:

- Replacing hardware
- Reinstalling the operating system
- Moving adapters between USB ports
- Changing drivers
- Booting without all adapters connected

Always verify interface assignments before enabling AP controls.

### Recommended Address Plan

```text
Host/uplink interface:  wlan1
Host address:            Assigned by the upstream router

Toolkit AP interface:   wlan2
Toolkit AP address:     10.42.0.1/24
Toolkit AP subnet:      10.42.0.0/24
Toolkit AP SSID:        PineApplePi-Toolkit
Toolkit AP band:        2.4 GHz
Toolkit AP channel:     6

Inventory interface:    wlan0
```

When PineApple-Pi runs on port `8000`, clients connected directly to the access point can use:

```text
http://10.42.0.1:8000/
```

Devices on the upstream local network can normally use:

```text
http://pineapplepi.local:8000/
```

The `.local` address requires working mDNS support on both the Raspberry Pi and client device.

---

## Hardware Requirements

### Minimum Hardware

- Raspberry Pi capable of running a 64-bit Raspberry Pi operating system
- Reliable microSD card or supported SSD
- Stable power supply appropriate for the Raspberry Pi model
- One working management network connection
- Keyboard and display access, SSH, or Raspberry Pi Connect for installation

### Recommended Three-Radio Build

- Raspberry Pi built-in Wi-Fi radio
- 2.4 GHz USB Wi-Fi adapter for host/uplink use
- AP-capable USB Wi-Fi adapter for `wlan2`
- Powered USB hub if the Pi cannot reliably power both adapters
- Adequate cooling for sustained operation

### Verify Connected Hardware

```bash
ip -brief link
iw dev
nmcli device status
lsusb
```

### Identify Adapter Drivers

```bash
ethtool -i wlan1
ethtool -i wlan2
```

### Verify AP Capability

First identify the physical wireless device associated with `wlan2`:

```bash
iw dev
```

Then inspect its capabilities. Replace `phy3` if necessary:

```bash
iw phy phy3 info |
sed -n '/Supported interface modes:/,/Band 1:/p'
```

The output must include:

```text
* AP
```

---

## Software Requirements

The current prototype targets:

- Debian 13 Trixie
- Raspberry Pi OS 64-bit
- Python 3.11 or newer
- NetworkManager
- `nmcli`
- `iproute2`
- Git
- Python virtual environments
- Avahi for `.local` discovery

Install the base packages:

```bash
sudo apt update

sudo apt install -y \
  git \
  python3-venv \
  python3-pip \
  network-manager \
  iw \
  iproute2 \
  usbutils \
  ethtool \
  rfkill \
  avahi-daemon \
  libnss-mdns
```

Enable mDNS hostname discovery:

```bash
sudo systemctl enable --now avahi-daemon
```

Verify:

```bash
systemctl is-active avahi-daemon
getent hosts pineapplepi.local
```

---

## Download Options

### Option A: GitHub Release

Prepared builds are published on the Releases page:

[Download PineApple-Pi Releases](https://github.com/Ghost0Mod3/PineApple-Pi/releases)

A prepared release asset may have a name such as:

```text
PineApple-Pi-v0.6.5-docs.zip
```

Release ZIP files are recommended for testers because they preserve a specific prepared version of the project.

### Option B: Clone the Repository

```bash
cd ~

git clone https://github.com/Ghost0Mod3/PineApple-Pi.git

cd PineApple-Pi
```

Verify the clone:

```bash
git status
git remote -v
find . -maxdepth 3 -type f | sort
```

---

## Quick Start

### 1. Enter the Project Directory

```bash
cd ~/PineApple-Pi
```

Confirm:

```bash
pwd
ls -la
```

The directory should contain:

```text
backend/
database/
frontend/
scripts/
tests/
.env.example
requirements.txt
requirements-dev.txt
README.md
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Confirm the active interpreter:

```bash
which python
```

Expected structure:

```text
/home/ghost0mod3/PineApple-Pi/.venv/bin/python
```

### 3. Install Python Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

### 4. Create the Local Configuration

```bash
cp .env.example .env
chmod 600 .env
```

Confirm:

```bash
ls -la .env
```

Expected permissions:

```text
-rw-------
```

### 5. Initialize the Database

```bash
python -m backend.cli
```

Expected output:

```text
Database initialized
```

### 6. Run Tests

```bash
pytest -q
```

### 7. Start the Development Server

```bash
uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port 8001
```

Open:

```text
http://PI-IP-ADDRESS:8001/
```

For the current development network, the host interface previously received:

```text
192.168.4.30
```

That would make the development address:

```text
http://192.168.4.30:8001/
```

Do not assume that address will remain the same on another network.

### Development Helper

The included helper automates environment creation, dependency installation, database initialization, and development startup:

```bash
chmod +x scripts/deploy-dev.sh
./scripts/deploy-dev.sh
```

---

## First-Time Administrator Setup

On the first browser visit:

1. Review the authorized-use and liability notice.
2. Accept the acknowledgment.
3. Create an administrator username.
4. Create a password containing at least 12 characters.
5. Sign in to the dashboard.
6. Create an Authorization Project before using assessment-oriented workflows.

Administrator passwords are stored as Argon2 hashes rather than plaintext.

> [!WARNING]
> The prototype currently runs over HTTP. Restrict HTTP-only deployments to trusted management networks until HTTPS is configured.

---

## Configuration

PineApple-Pi loads local settings from `.env`.

Example:

```ini
APP_VERSION=0.6.5-docs
DATABASE_PATH=database/pineapple_pi.db
FRONTEND_PATH=frontend

HOST_INTERFACE=wlan1
ACCESS_POINT_INTERFACE=wlan2
INVENTORY_INTERFACE=wlan0

SESSION_COOKIE_NAME=pineapple_session

ENABLE_AP_CHANGES=false
AP_CONNECTION_NAME=PineApple-AP
```

### `APP_VERSION`

Version returned by the health endpoint.

```ini
APP_VERSION=0.6.5-docs
```

### `DATABASE_PATH`

Path to the SQLite database.

```ini
DATABASE_PATH=database/pineapple_pi.db
```

Relative paths are resolved from the project directory.

### `FRONTEND_PATH`

Directory containing the frontend files.

```ini
FRONTEND_PATH=frontend
```

### `HOST_INTERFACE`

Primary host and Internet uplink.

```ini
HOST_INTERFACE=wlan1
```

The host interface should carry:

- SSH
- Raspberry Pi Connect
- Internet access
- Package downloads
- Git operations
- Normal Pi administration

### `ACCESS_POINT_INTERFACE`

Dedicated access-point interface.

```ini
ACCESS_POINT_INTERFACE=wlan2
```

The prototype AP backend is deliberately restricted to `wlan2`.

### `INVENTORY_INTERFACE`

Interface reserved for authorized network inventory workflows.

```ini
INVENTORY_INTERFACE=wlan0
```

### `SESSION_COOKIE_NAME`

Name of the administrator session cookie.

```ini
SESSION_COOKIE_NAME=pineapple_session
```

### `ENABLE_AP_CHANGES`

Controls whether the Settings page can modify NetworkManager.

Safe prototype default:

```ini
ENABLE_AP_CHANGES=false
```

After verifying adapter assignments:

```ini
ENABLE_AP_CHANGES=true
```

Restart PineApple-Pi after changing `.env`.

### `AP_CONNECTION_NAME`

NetworkManager profile managed by PineApple-Pi:

```ini
AP_CONNECTION_NAME=PineApple-AP
```

---

## Host and Uplink Configuration

The recommended host interface is `wlan1`.

Check status:

```bash
nmcli device status
```

Expected structure:

```text
wlan1  wifi  connected  PineApple-Host
wlan2  wifi  disconnected
wlan0  wifi  connected or disconnected
```

Check addresses:

```bash
ip -4 -brief address show wlan1
```

Check link quality:

```bash
iw dev wlan1 link
```

Check default routes:

```bash
ip route show default
```

The preferred host route should have the lower metric:

```text
default via ROUTER-IP dev wlan1 metric 50
```

Check the route selected for Internet traffic:

```bash
ip route get 1.1.1.1
```

The response should show:

```text
dev wlan1
```

---

## Open AP Controls

The Settings page can configure an open access point on `wlan2`.

### Default AP Configuration

```text
SSID:             PineApplePi-Toolkit
Interface:        wlan2
Band:             2.4 GHz
Channel:          6
Address:          10.42.0.1/24
Internet sharing: Enabled
Client isolation: Enabled
Wi-Fi password:   None
```

### Supported Prototype Channels

```text
2.4 GHz: 1, 6, 11
5 GHz:   36, 40, 44, 48
```

The default is:

```text
2.4 GHz channel 6
```

### Open-Network Confirmation

To configure the AP, the administrator must:

1. Select **Open network, no password**.
2. Select the desired band and channel.
3. Keep client isolation enabled.
4. Type the exact confirmation phrase:

```text
OPEN NETWORK
```

5. Save the AP profile.
6. Start the AP.

### Open-AP Warning

An open access point has no Wi-Fi password.

Anyone within radio range may attempt to connect.

Recommended precautions:

- Keep client isolation enabled.
- Do not expose unrelated services to `wlan2`.
- Keep the dashboard administrator account protected.
- Stop the AP when testing is complete.
- Review the AP Activity Log regularly.
- Add firewall rules before public or unattended deployment.
- Do not use open mode for sensitive traffic.

---

## Manual AP Verification

Check `wlan2`:

```bash
nmcli device status
ip -4 -brief address show wlan2
iw dev wlan2 info
```

Expected address:

```text
10.42.0.1/24
```

Expected operating mode:

```text
type AP
```

Expected channel:

```text
channel 6
```

Check routing:

```bash
ip route show
ip route get 1.1.1.1
```

Outbound Internet traffic should continue to use `wlan1`.

---

## AP Activity Log

The Settings page includes an activity panel for devices observed on `wlan2`.

### Displayed Client Information

For every observed AP client, PineApple-Pi can display:

- Client IP address
- Client MAC address
- DHCP hostname when available
- Interface name
- First-seen timestamp
- Last-seen timestamp
- Neighbor state
- Online or offline status
- Connection event
- Disconnection event

### Data Sources

The backend combines information from the Linux neighbor table:

```bash
ip -4 neigh show dev wlan2
```

with NetworkManager-managed DHCP lease information when available.

### Check Current Clients Manually

```bash
ip -4 neigh show dev wlan2
```

Example structure:

```text
10.42.0.20 lladdr aa:bb:cc:dd:ee:ff REACHABLE
```

This represents:

```text
IP address:  10.42.0.20
MAC address: aa:bb:cc:dd:ee:ff
State:       REACHABLE
```

### Hostname Availability

A hostname appears only when the connected device provides one through DHCP.

Some devices:

- Do not provide a hostname
- Use generic hostnames
- Randomize MAC addresses
- Change MAC addresses between connections

The dashboard may therefore show:

```text
Hostname: Unknown
```

### Activity History

The database records:

- Connected events
- Disconnected events
- IP address
- MAC address
- Hostname when available
- Event timestamp
- Interface name

### Clear Activity

Use **Clear log** in Settings to remove stored AP client and event records.

### Information Not Collected

The AP Activity feature does not intentionally collect:

- Wi-Fi passwords
- Website contents
- Browser history
- Message contents
- Account credentials
- Client files
- Full packet captures

---

## Liability and Authorization

The entry screen includes an authorized-use and liability acknowledgment.

The acknowledgment states that the toolkit is intended for:

- Systems owned by the operator
- Networks owned by the operator
- Systems covered by explicit authorization
- Networks covered by explicit authorization
- Controlled learning environments

The acknowledgment does not create authorization by itself.

The operator remains responsible for:

- Defining project scope
- Following applicable laws
- Following organizational policies
- Protecting client data
- Avoiding disruption
- Retaining only necessary records
- Stopping activity when authorization expires

---

## Authorization Projects

Authorization Projects provide an administrative record describing why a workflow is being used.

Each project records:

- Project name
- Authorizing owner or party
- Exact scope
- Expiration date
- Active state

### Recommended Scope Contents

A useful scope should identify:

- Included systems
- Included networks
- Excluded systems
- Excluded networks
- Permitted activities
- Prohibited activities
- Authorized time window
- Data-retention expectations
- Contact information for the authorizing party

### Example Scope

```text
Inventory is limited to the privately owned 192.168.4.0/22 lab network.

Permitted activities include host discovery, identifying device addresses,
and reviewing exposed service information.

Credential testing, disruption, deauthentication, traffic interception,
and testing against third-party systems are excluded.

Authorization expires on the project expiration date.
```

---

## Toolkit Page

The prototype Toolkit page includes cards for:

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

The dashboard checks for selected local executables and displays:

```text
Installed
```

or:

```text
Not installed
```

Individual guided execution adapters are still being developed.

---

## Downloads Page

The Downloads page displays reviewed installation plans for registered tools.

The prototype does not automatically execute:

- `apt`
- `pip`
- `pipx`
- Docker builds
- Third-party shell scripts
- Arbitrary root commands

Package installation should be performed from an authenticated shell until each tool installer has:

- Package-name validation
- Operating-system validation
- Architecture checks
- Installation logging
- Failure handling
- Rollback handling
- Version reporting

---

## Database

PineApple-Pi uses SQLite.

Default database path:

```text
database/pineapple_pi.db
```

Stored records include:

- Administrator users
- Session hashes
- Liability acknowledgments
- Authorization projects
- AP clients
- AP connection events

The database is excluded from Git using `.gitignore`.

### Back Up the Database

Stop the service:

```bash
sudo systemctl stop pineapple-pi-api.service
```

Copy the database:

```bash
cp database/pineapple_pi.db \
  ~/pineapple-pi-db-backup.sqlite
```

Start the service again:

```bash
sudo systemctl start pineapple-pi-api.service
```

Protect database backups because they may contain:

- Usernames
- Authorization scope
- Client IP addresses
- Client MAC addresses
- Hostnames
- Connection timestamps

---

## Production Service

Development mode uses port `8001`.

A persistent deployment can run on port `8000` with systemd.

Create:

```text
/etc/systemd/system/pineapple-pi-api.service
```

Example:

```ini
[Unit]
Description=PineApple-Pi Guided Dashboard
After=network-online.target avahi-daemon.service
Wants=network-online.target

[Service]
Type=simple
User=ghost0mod3
Group=ghost0mod3
WorkingDirectory=/home/ghost0mod3/PineApple-Pi
EnvironmentFile=/home/ghost0mod3/PineApple-Pi/.env
ExecStart=/home/ghost0mod3/PineApple-Pi/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable and start:

```bash
sudo systemctl enable --now pineapple-pi-api.service
```

Check status:

```bash
sudo systemctl status \
  pineapple-pi-api.service \
  --no-pager
```

View recent logs:

```bash
sudo journalctl \
  -u pineapple-pi-api.service \
  -n 100 \
  --no-pager
```

Test health:

```bash
curl http://127.0.0.1:8000/healthz
```

Expected structure:

```json
{"status":"ok","version":"0.6.5-docs"}
```

Check the listening port:

```bash
sudo ss -ltnp | grep ':8000'
```

---

## Dashboard Entry Points

### Upstream Network

```text
http://pineapplepi.local:8000/
```

### Host IP Fallback

```text
http://HOST-IP-ADDRESS:8000/
```

### Direct AP Connection

```text
http://10.42.0.1:8000/
```

### Development Port

```text
http://HOST-IP-ADDRESS:8001/
```

---

## Updating from GitHub

### Preserve Local State

Before updating, back up:

```text
.env
database/pineapple_pi.db
```

### Normal Git Update

```bash
cd ~/PineApple-Pi

git pull

source .venv/bin/activate

python -m pip install \
  -r requirements.txt

python -m backend.cli

sudo systemctl restart \
  pineapple-pi-api.service
```

### Force Local Source to Match GitHub

> [!CAUTION]
> This discards local changes to tracked files.

```bash
cd ~/PineApple-Pi

git fetch origin

git reset --hard origin/main
```

Local files ignored by Git, including `.env`, are normally unaffected, but always make a backup first.

### Release ZIP Update

1. Download the new ZIP from GitHub Releases.
2. Stop the PineApple-Pi service.
3. Back up `.env`.
4. Back up the SQLite database.
5. Extract the new release into a separate directory.
6. Review the release notes.
7. Copy the existing `.env` only if the variables remain compatible.
8. Restore the database only if the schema remains compatible.
9. Recreate or update the virtual environment.
10. Run tests.
11. Start the new build on port `8001`.
12. Replace the production

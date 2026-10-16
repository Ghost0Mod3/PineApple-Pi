#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]]||{ echo 'Run with sudo';exit 1; }
apt-get update
apt-get install -y tshark tcpdump nmap arp-scan lynis rtl-sdr docker.io pipx
sudo -u "${SUDO_USER:-ghost0mod3}" pipx install "meshtastic[cli]" || true
echo 'Base tools installed. OSINT containers and Node-RED require separate review.'

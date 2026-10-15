#!/usr/bin/env bash
set -Eeuo pipefail
nmcli --fields IN-USE,BSSID,SSID,CHAN,FREQ,SIGNAL,SECURITY device wifi list ifname wlan1 --rescan yes

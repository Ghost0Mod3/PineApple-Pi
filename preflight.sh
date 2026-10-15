#!/usr/bin/env bash
set -u
echo "Pineapple-Pi preflight"
echo "======================"
hostname
nmcli device status
ip route show default
rpi-connect status 2>&1 || true
echo
printf 'wlan1 MAC: '; cat /sys/class/net/wlan1/address 2>/dev/null || echo missing
printf 'wlan1 driver: '; basename "$(readlink -f /sys/class/net/wlan1/device/driver 2>/dev/null)" 2>/dev/null || echo missing

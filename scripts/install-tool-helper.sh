#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]]||{ echo 'Run with sudo' >&2;exit 1; }
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.."&&pwd);USER_NAME=${SUDO_USER:-ghost0mod3}
install -o root -g root -m755 "$ROOT/scripts/pineapple-tool-installer" /usr/local/sbin/pineapple-tool-installer
printf 'INSTALL_USER=%q\n' "$USER_NAME">/etc/pineapple-pi-installer.conf;chmod 600 /etc/pineapple-pi-installer.conf
cat >/etc/sudoers.d/pineapple-pi-installer <<EOF
$USER_NAME ALL=(root) NOPASSWD: /usr/local/sbin/pineapple-tool-installer install *
EOF
chmod 440 /etc/sudoers.d/pineapple-pi-installer;visudo -cf /etc/sudoers.d/pineapple-pi-installer
mkdir -p /etc/systemd/system/pineapple-pi-api.service.d;cat >/etc/systemd/system/pineapple-pi-api.service.d/tool-installer.conf <<EOF
[Service]
NoNewPrivileges=false
EOF
systemctl daemon-reload;/usr/local/sbin/pineapple-tool-installer issue-token

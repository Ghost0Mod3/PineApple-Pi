#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

APP_NAME="pineapple-pi"
APP_DIR="/opt/pineapple-pi"
SERVICE_NAME="pineapple-pi-api.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"
BACKUP_ROOT="/var/backups/pineapple-pi"
PORT="${PINEAPPLE_PORT:-8000}"
HEALTH_URL="http://127.0.0.1:${PORT}/healthz"
SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
INSTALL_USER="${SUDO_USER:-${USER:-}}"
BACKUP_DIR=""
NEW_UNIT_WRITTEN=0
OLD_SERVICE_WAS_ACTIVE=0

log()  { printf '\n[+] %s\n' "$*"; }
warn() { printf '\n[!] %s\n' "$*" >&2; }
die()  { printf '\n[x] %s\n' "$*" >&2; exit 1; }

require_root() {
  [[ ${EUID} -eq 0 ]] || die "Run this installer with: sudo ./install.sh"
  [[ -n "${INSTALL_USER}" ]] || die "Could not determine the non-root service user."
  id "${INSTALL_USER}" >/dev/null 2>&1 || die "User '${INSTALL_USER}' does not exist."
}

validate_source() {
  log "Validating repository source"
  local required=(
    "backend/main.py"
    "backend/cli.py"
    "frontend/index.html"
    "database/schema.sql"
    "requirements.txt"
  )
  local item
  for item in "${required[@]}"; do
    [[ -e "${SOURCE_DIR}/${item}" ]] || die "Missing required file: ${item}"
  done

  /usr/bin/python3 -m py_compile "${SOURCE_DIR}"/backend/*.py
  /bin/bash -n "${SOURCE_DIR}/install.sh"

  if [[ -f "${SOURCE_DIR}/frontend/assets/app.js" ]] && command -v node >/dev/null 2>&1; then
    node --check "${SOURCE_DIR}/frontend/assets/app.js"
  fi
}

check_power_warning() {
  if command -v vcgencmd >/dev/null 2>&1; then
    local value
    value="$(vcgencmd get_throttled 2>/dev/null || true)"
    if [[ "${value}" != "throttled=0x0" && -n "${value}" ]]; then
      warn "Raspberry Pi power warning: ${value}"
      warn "Installation may continue, but wlan2/AP activation must remain disabled until power is stable."
    fi
  fi
}

install_packages() {
  log "Installing required Debian packages"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    network-manager iw iproute2 \
    avahi-daemon libnss-mdns \
    curl rsync ca-certificates
}

make_backup() {
  log "Creating rollback backup"
  install -d -m 0700 "${BACKUP_ROOT}"
  BACKUP_DIR="${BACKUP_ROOT}/$(date -u +%Y%m%dT%H%M%SZ)"
  install -d -m 0700 "${BACKUP_DIR}"

  if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
    OLD_SERVICE_WAS_ACTIVE=1
  fi

  if [[ -d "${APP_DIR}" ]]; then
    cp -a "${APP_DIR}" "${BACKUP_DIR}/app"
  fi
  if [[ -f "${SERVICE_FILE}" ]]; then
    cp -a "${SERVICE_FILE}" "${BACKUP_DIR}/${SERVICE_NAME}"
  fi
  printf '%s\n' "${OLD_SERVICE_WAS_ACTIVE}" > "${BACKUP_DIR}/service-was-active"
}

restore_backup() {
  local rc=$?
  trap - ERR
  warn "Installation failed with exit code ${rc}. Rolling back."

  systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
  rm -rf "${APP_DIR}"

  if [[ -n "${BACKUP_DIR}" && -d "${BACKUP_DIR}/app" ]]; then
    cp -a "${BACKUP_DIR}/app" "${APP_DIR}"
  fi

  if [[ -n "${BACKUP_DIR}" && -f "${BACKUP_DIR}/${SERVICE_NAME}" ]]; then
    cp -a "${BACKUP_DIR}/${SERVICE_NAME}" "${SERVICE_FILE}"
  elif [[ ${NEW_UNIT_WRITTEN} -eq 1 ]]; then
    rm -f "${SERVICE_FILE}"
  fi

  systemctl daemon-reload || true
  if [[ ${OLD_SERVICE_WAS_ACTIVE} -eq 1 ]]; then
    systemctl start "${SERVICE_NAME}" || true
  fi

  warn "Rollback finished. Backup: ${BACKUP_DIR:-none}"
  exit "${rc}"
}

stage_application() {
  log "Staging application in ${APP_DIR}"
  local preserved_env=""
  local preserved_db=""

  if [[ -f "${APP_DIR}/.env" ]]; then
    preserved_env="$(mktemp)"
    cp -a "${APP_DIR}/.env" "${preserved_env}"
  elif [[ -f "${SOURCE_DIR}/.env" ]]; then
    preserved_env="$(mktemp)"
    cp -a "${SOURCE_DIR}/.env" "${preserved_env}"
  fi

  if [[ -f "${APP_DIR}/database/pineapple_pi.db" ]]; then
    preserved_db="$(mktemp)"
    cp -a "${APP_DIR}/database/pineapple_pi.db" "${preserved_db}"
  elif [[ -f "${SOURCE_DIR}/database/pineapple_pi.db" ]]; then
    preserved_db="$(mktemp)"
    cp -a "${SOURCE_DIR}/database/pineapple_pi.db" "${preserved_db}"
  fi

  rm -rf "${APP_DIR}"
  install -d -m 0755 "${APP_DIR}"

  rsync -a --delete \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '.env' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'database/*.db' \
    --exclude 'database/*.db-*' \
    --exclude 'data/artifacts/*' \
    --exclude 'logs/*' \
    "${SOURCE_DIR}/" "${APP_DIR}/"

  install -d -o "${INSTALL_USER}" -g "${INSTALL_USER}" -m 0750 \
    "${APP_DIR}/database" "${APP_DIR}/data" \
    "${APP_DIR}/data/artifacts" "${APP_DIR}/data/backups" \
    "${APP_DIR}/logs"

  if [[ -n "${preserved_env}" ]]; then
    install -o "${INSTALL_USER}" -g "${INSTALL_USER}" -m 0600 \
      "${preserved_env}" "${APP_DIR}/.env"
    rm -f "${preserved_env}"
  elif [[ -f "${APP_DIR}/.env.example" ]]; then
    install -o "${INSTALL_USER}" -g "${INSTALL_USER}" -m 0600 \
      "${APP_DIR}/.env.example" "${APP_DIR}/.env"
  else
    cat > "${APP_DIR}/.env" <<'ENVEOF'
APP_VERSION=development
DATABASE_PATH=database/pineapple_pi.db
FRONTEND_PATH=frontend
HOST_INTERFACE=wlan1
ACCESS_POINT_INTERFACE=wlan2
INVENTORY_INTERFACE=wlan0
SESSION_COOKIE_NAME=pineapple_session
ENABLE_AP_CHANGES=false
AP_CONNECTION_NAME=PineApple-AP
ENVEOF
    chown "${INSTALL_USER}:${INSTALL_USER}" "${APP_DIR}/.env"
    chmod 0600 "${APP_DIR}/.env"
  fi

  if [[ -n "${preserved_db}" ]]; then
    install -o "${INSTALL_USER}" -g "${INSTALL_USER}" -m 0600 \
      "${preserved_db}" "${APP_DIR}/database/pineapple_pi.db"
    rm -f "${preserved_db}"
  fi

  # Safety default: installer never enables AP changes.
  if grep -q '^ENABLE_AP_CHANGES=' "${APP_DIR}/.env"; then
    sed -i 's/^ENABLE_AP_CHANGES=.*/ENABLE_AP_CHANGES=false/' "${APP_DIR}/.env"
  else
    printf '\nENABLE_AP_CHANGES=false\n' >> "${APP_DIR}/.env"
  fi

  chown -R "${INSTALL_USER}:${INSTALL_USER}" "${APP_DIR}"
  chmod 0600 "${APP_DIR}/.env"
}

create_venv() {
  log "Creating isolated Python environment"
  sudo -u "${INSTALL_USER}" python3 -m venv "${APP_DIR}/.venv"
  sudo -u "${INSTALL_USER}" "${APP_DIR}/.venv/bin/python" -m pip install --upgrade pip
  sudo -u "${INSTALL_USER}" "${APP_DIR}/.venv/bin/python" -m pip install \
    --requirement "${APP_DIR}/requirements.txt"
}

validate_application() {
  log "Validating Python application and database"
  cd "${APP_DIR}"
  sudo -u "${INSTALL_USER}" "${APP_DIR}/.venv/bin/python" -m py_compile backend/*.py
  sudo -u "${INSTALL_USER}" "${APP_DIR}/.venv/bin/python" -c \
    'from backend.main import app; assert app is not None'

  # Supports the current CLI form; if it requires init-db, retry that form.
  if ! sudo -u "${INSTALL_USER}" "${APP_DIR}/.venv/bin/python" -m backend.cli; then
    sudo -u "${INSTALL_USER}" "${APP_DIR}/.venv/bin/python" -m backend.cli init-db
  fi

  [[ -f "${APP_DIR}/database/pineapple_pi.db" ]] || \
    die "Database initialization did not create database/pineapple_pi.db"
}

write_service() {
  log "Installing systemd service"
  cat > "${SERVICE_FILE}" <<UNITEOF
[Unit]
Description=PineApple-Pi Guided Dashboard
After=network-online.target NetworkManager.service avahi-daemon.service
Wants=network-online.target

[Service]
Type=simple
User=${INSTALL_USER}
Group=${INSTALL_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
Restart=on-failure
RestartSec=5
TimeoutStopSec=15
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=${APP_DIR}/database ${APP_DIR}/data ${APP_DIR}/logs
UMask=0077

[Install]
WantedBy=multi-user.target
UNITEOF
  chmod 0644 "${SERVICE_FILE}"
  NEW_UNIT_WRITTEN=1
  systemctl daemon-reload
}

start_and_verify() {
  log "Starting PineApple-Pi"
  systemctl enable "${SERVICE_NAME}"
  systemctl restart "${SERVICE_NAME}"

  local attempt
  for attempt in $(seq 1 20); do
    if curl --fail --silent --show-error --max-time 2 "${HEALTH_URL}" >/tmp/pineapple-health.json; then
      printf '\nHealth response: '
      cat /tmp/pineapple-health.json
      printf '\n'
      rm -f /tmp/pineapple-health.json
      return 0
    fi
    sleep 1
  done

  journalctl -u "${SERVICE_NAME}" -n 80 --no-pager || true
  die "Health check failed at ${HEALTH_URL}"
}

main() {
  require_root
  trap restore_backup ERR
  validate_source
  check_power_warning
  install_packages
  make_backup
  stage_application
  create_venv
  validate_application
  write_service
  start_and_verify
  trap - ERR

  log "Installation completed safely"
  printf '%s\n' \
    "Dashboard: http://pineapplepi.local:${PORT}/" \
    "IP fallback: http://192.168.4.30:${PORT}/" \
    "Application: ${APP_DIR}" \
    "Backup: ${BACKUP_DIR}" \
    "AP changes: disabled"
}

main "$@"

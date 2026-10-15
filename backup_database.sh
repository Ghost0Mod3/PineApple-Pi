#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/backups
stamp=$(date -u +%Y%m%dT%H%M%SZ)
sqlite3 database/pineapple_pi.db ".backup 'data/backups/pineapple_pi-$stamp.db'"

#!/usr/bin/env bash
set -Eeuo pipefail

log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1"
}

log "Running healthcheck..."
curl -fsS http://127.0.0.1:8000/api/config > /dev/null
curl -fsS http://127.0.0.1:3100/health > /dev/null
echo "Healthcheck passed"

#!/usr/bin/env bash
set -Eeuo pipefail

log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1"
}

log "Deploy release..."

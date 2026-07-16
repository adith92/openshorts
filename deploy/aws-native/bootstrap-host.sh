#!/usr/bin/env bash
set -Eeuo pipefail

log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1"
}

log "Starting bootstrap process..."

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git sudo jq curl software-properties-common

if ! id "openshorts" &>/dev/null; then
    log "Creating openshorts service user..."
    useradd -r -d /var/lib/openshorts -s /bin/bash openshorts
fi

mkdir -p /var/lib/openshorts
chown openshorts:openshorts /var/lib/openshorts

REPO_URL="https://github.com/adith92/openshorts.git"
BRANCH="deploy/aws-native"
TARGET_DIR="/var/lib/openshorts"

if [ -d "$TARGET_DIR/.git" ]; then
    log "Repository already exists. Pulling latest changes..."
    sudo -u openshorts -H bash -c "cd $TARGET_DIR && git fetch origin && git checkout $BRANCH && git reset --hard origin/$BRANCH && git pull origin $BRANCH"
else
    log "Cloning repository..."
    if [ "$(ls -A $TARGET_DIR)" ]; then
        TMP_CLONE=$(mktemp -d)
        git clone -b "$BRANCH" "$REPO_URL" "$TMP_CLONE"
        cp -a $TMP_CLONE/. $TARGET_DIR/
        rm -rf "$TMP_CLONE"
        chown -R openshorts:openshorts "$TARGET_DIR"
    else
        sudo -u openshorts -H bash -c "git clone -b $BRANCH $REPO_URL $TARGET_DIR"
    fi
fi

log "Running deploy-release.sh..."
cd "$TARGET_DIR/deploy/aws-native"
chmod +x deploy-release.sh
./deploy-release.sh

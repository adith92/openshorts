#!/usr/bin/env bash
set -Eeuo pipefail

log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1"
}

log "Deploy release..."

export DEBIAN_FRONTEND=noninteractive

# 1. Install dependencies
log "Installing OS dependencies..."
add-apt-repository -y ppa:deadsnakes/ppa
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3.11-dev nodejs ffmpeg imagemagick nginx build-essential

# 2. Setup virtual environment
log "Setting up Python virtual environment..."
cd /var/lib/openshorts
sudo -u openshorts -H bash -c "python3.11 -m venv .venv"
sudo -u openshorts -H bash -c ".venv/bin/pip install --upgrade pip"
sudo -u openshorts -H bash -c ".venv/bin/pip install -r requirements.txt"

# 3. Build frontend and renderer
log "Building Node.js apps..."
sudo -u openshorts -H bash -c "cd dashboard && npm ci && npm run build"
sudo -u openshorts -H bash -c "cd render-service && npm ci && npm run build"
sudo -u openshorts -H bash -c "cd remotion && npm ci"

# 4. Setup Nginx
log "Configuring Nginx..."
cp deploy/aws-native/nginx-openshorts.conf /etc/nginx/sites-available/openshorts
ln -sf /etc/nginx/sites-available/openshorts /etc/nginx/sites-enabled/openshorts
rm -f /etc/nginx/sites-enabled/default

# 5. Setup Systemd services
log "Configuring Systemd..."
cp deploy/aws-native/openshorts-backend.service /etc/systemd/system/
cp deploy/aws-native/openshorts-renderer.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable nginx openshorts-backend openshorts-renderer
systemctl restart nginx openshorts-backend openshorts-renderer

# 6. Verify health
log "Waiting for services to start..."
sleep 5
systemctl status openshorts-backend --no-pager
systemctl status openshorts-renderer --no-pager

log "Running healthcheck..."
chmod +x deploy/aws-native/healthcheck.sh
sudo -u openshorts ./deploy/aws-native/healthcheck.sh

log "Deployment complete."

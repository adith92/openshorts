#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/aws-native/prepare-host-layout.sh" >&2
  exit 1
fi

APP_ROOT="${APP_ROOT:-/opt/openshorts}"
SERVICE_HOME="${SERVICE_HOME:-/var/lib/openshorts}"

if ! id openshorts >/dev/null 2>&1; then
  useradd \
    --system \
    --create-home \
    --home-dir "$SERVICE_HOME" \
    --shell /bin/bash \
    openshorts
  passwd -l openshorts
fi

install -d -o openshorts -g openshorts -m 0750 \
  "$APP_ROOT" \
  "$SERVICE_HOME/uploads" \
  "$SERVICE_HOME/output"

install -d -o openshorts -g openshorts -m 0700 \
  "$SERVICE_HOME/.gemini" \
  "$SERVICE_HOME/tmp/gemini-cli"

install -d -o root -g openshorts -m 0750 /etc/openshorts

for runtime_name in uploads output; do
  source_path="$APP_ROOT/$runtime_name"
  target_path="$SERVICE_HOME/$runtime_name"

  if [[ -e "$source_path" && ! -L "$source_path" ]]; then
    if [[ -d "$source_path" ]] && [[ -n "$(find "$source_path" -mindepth 1 -print -quit)" ]]; then
      archive_path="$SERVICE_HOME/${runtime_name}.migration.$(date +%Y%m%d-%H%M%S)"
      mv "$source_path" "$archive_path"
      echo "Moved existing $source_path to $archive_path"
    else
      rm -rf "$source_path"
    fi
  fi

  ln -sfn "$target_path" "$source_path"
  chown -h openshorts:openshorts "$source_path"
done

chown -R openshorts:openshorts "$SERVICE_HOME"
chmod 0700 "$SERVICE_HOME/.gemini" "$SERVICE_HOME/tmp/gemini-cli"

echo "Native OpenShorts host layout is ready."
echo "Runtime media: $SERVICE_HOME/uploads and $SERVICE_HOME/output"
echo "Gemini OAuth: $SERVICE_HOME/.gemini"

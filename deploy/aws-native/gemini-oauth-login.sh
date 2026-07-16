#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this script as root through AWS Systems Manager:" >&2
  echo "  sudo bash deploy/aws-native/gemini-oauth-login.sh" >&2
  exit 1
fi

if ! id openshorts >/dev/null 2>&1; then
  echo "Linux user 'openshorts' does not exist." >&2
  exit 1
fi

GEMINI_BIN="${GEMINI_CLI_BINARY:-/usr/local/bin/gemini}"
if [[ ! -x "$GEMINI_BIN" ]]; then
  echo "Gemini CLI was not found at $GEMINI_BIN" >&2
  echo "Install it with: sudo npm install -g @google/gemini-cli@latest" >&2
  exit 1
fi

install -d -o openshorts -g openshorts -m 0700 \
  /var/lib/openshorts/.gemini \
  /var/lib/openshorts/tmp/gemini-cli

echo "Starting the official Gemini CLI as Linux user 'openshorts'."
echo "Open the URL shown below in your local browser and complete Google sign-in."
echo "OAuth credentials will remain on the VPS under /var/lib/openshorts/.gemini."
echo

sudo -u openshorts -H env \
  HOME=/var/lib/openshorts \
  NO_BROWSER=true \
  GOOGLE_GENAI_USE_GCA=true \
  GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true \
  GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli \
  "$GEMINI_BIN"

chown -R openshorts:openshorts /var/lib/openshorts/.gemini
chmod 0700 /var/lib/openshorts/.gemini
find /var/lib/openshorts/.gemini -type d -exec chmod 0700 {} +
find /var/lib/openshorts/.gemini -type f -exec chmod 0600 {} +

echo
echo "OAuth login command finished. Verify it with:"
echo "  sudo bash deploy/aws-native/gemini-oauth-check.sh"

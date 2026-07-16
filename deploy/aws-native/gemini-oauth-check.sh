#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/aws-native/gemini-oauth-check.sh" >&2
  exit 1
fi

GEMINI_BIN="${GEMINI_CLI_BINARY:-/usr/local/bin/gemini}"
CREDENTIAL_DIR="${GEMINI_CLI_CREDENTIAL_DIR:-/var/lib/openshorts/.gemini}"
WORK_DIR="${GEMINI_CLI_WORKING_DIR:-/var/lib/openshorts/tmp/gemini-cli}"

if [[ ! -x "$GEMINI_BIN" ]]; then
  echo "FAIL: Gemini CLI is not installed at $GEMINI_BIN" >&2
  exit 1
fi

if [[ ! -d "$CREDENTIAL_DIR" ]] || ! find "$CREDENTIAL_DIR" -type f -print -quit | grep -q .; then
  echo "FAIL: no persistent OAuth credential files were found." >&2
  echo "Run: sudo bash deploy/aws-native/gemini-oauth-login.sh" >&2
  exit 1
fi

install -d -o openshorts -g openshorts -m 0700 "$WORK_DIR"
TMP_OUTPUT="$(mktemp)"
trap 'rm -f "$TMP_OUTPUT"' EXIT

if ! sudo -u openshorts -H env \
  HOME=/var/lib/openshorts \
  NO_BROWSER=true \
  GOOGLE_GENAI_USE_GCA=true \
  GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true \
  GEMINI_CLI_WORKING_DIR="$WORK_DIR" \
  "$GEMINI_BIN" \
  -p "Reply with exactly OPENSHORTS_OK" \
  --output-format json \
  --approval-mode plan \
  --skip-trust >"$TMP_OUTPUT" 2>&1; then
  echo "FAIL: Gemini CLI could not use the stored OAuth session." >&2
  echo "Run the one-time login again. Output was intentionally hidden to protect authentication data." >&2
  exit 1
fi

python3 - "$TMP_OUTPUT" <<'PY'
import json
import pathlib
import sys

text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").strip()
try:
    payload = json.loads(text)
except json.JSONDecodeError:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise SystemExit("FAIL: Gemini CLI did not return JSON")
    payload = json.loads(text[start:end + 1])

if payload.get("response", "").strip() != "OPENSHORTS_OK":
    raise SystemExit("FAIL: Gemini CLI returned an unexpected response")

print("PASS: persistent Gemini OAuth is ready for the OpenShorts service user")
PY

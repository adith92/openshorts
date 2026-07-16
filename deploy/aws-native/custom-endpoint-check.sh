#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${OPENSHORTS_ENV_FILE:-/etc/openshorts/openshorts.env}"

if [[ ! -r "$ENV_FILE" ]]; then
  echo "FAIL: cannot read $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

: "${AI_BASE_URL:?AI_BASE_URL is required in $ENV_FILE}"
: "${AI_API_KEY:?AI_API_KEY is required in $ENV_FILE}"
: "${AI_MODEL:?AI_MODEL is required in $ENV_FILE}"

API_ROOT="${AI_BASE_URL%/}"
API_ROOT="${API_ROOT%/chat/completions}"
API_ROOT="${API_ROOT%/models}"
MODELS_URL="$API_ROOT/models"
CHAT_URL="$API_ROOT/chat/completions"

TMP_MODELS="$(mktemp)"
TMP_CHAT="$(mktemp)"
trap 'rm -f "$TMP_MODELS" "$TMP_CHAT"' EXIT

if ! curl \
  --fail \
  --silent \
  --show-error \
  --max-time 30 \
  --header "Authorization: Bearer ${AI_API_KEY}" \
  --header "Accept: application/json" \
  "$MODELS_URL" >"$TMP_MODELS"; then
  echo "FAIL: could not fetch endpoint models" >&2
  exit 1
fi

python3 - "$TMP_MODELS" "$AI_MODEL" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
selected = sys.argv[2]

candidates = []
if isinstance(payload, list):
    candidates.extend(payload)
elif isinstance(payload, dict):
    for key in ("data", "models"):
        value = payload.get(key)
        if isinstance(value, list):
            candidates.extend(value)
    result = payload.get("result")
    if isinstance(result, dict):
        for key in ("data", "models"):
            value = result.get(key)
            if isinstance(value, list):
                candidates.extend(value)

ids = []
for item in candidates:
    if isinstance(item, str):
        value = item
    elif isinstance(item, dict):
        value = item.get("id") or item.get("name") or item.get("model") or item.get("slug")
    else:
        value = None
    if value:
        ids.append(str(value).strip())

if selected not in ids:
    raise SystemExit(f"FAIL: configured AI_MODEL was not returned by /models: {selected}")

print(f"PASS: configured model is available: {selected}")
PY

CHAT_PAYLOAD="$({
  AI_MODEL="$AI_MODEL" python3 - <<'PY'
import json
import os

print(json.dumps({
    "model": os.environ["AI_MODEL"],
    "messages": [
        {"role": "user", "content": "Reply with exactly OPENSHORTS_OK"}
    ],
    "max_tokens": 32,
}))
PY
})"

if ! curl \
  --fail \
  --silent \
  --show-error \
  --max-time 60 \
  --header "Authorization: Bearer ${AI_API_KEY}" \
  --header "Content-Type: application/json" \
  --data "$CHAT_PAYLOAD" \
  "$CHAT_URL" >"$TMP_CHAT"; then
  echo "FAIL: custom endpoint chat completion failed" >&2
  exit 1
fi

python3 - "$TMP_CHAT" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
try:
    content = payload["choices"][0]["message"]["content"]
except (KeyError, IndexError, TypeError):
    raise SystemExit("FAIL: response is missing choices[0].message.content")

if "OPENSHORTS_OK" not in str(content):
    raise SystemExit("FAIL: endpoint returned an unexpected smoke-test response")

print("PASS: custom endpoint model discovery and chat completion are ready")
PY

#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/clean-local-native.sh             # dry-run only
  scripts/clean-local-native.sh --apply     # remove generated build/cache artifacts
  scripts/clean-local-native.sh --apply --purge-runtime

The script never deletes .env, Gemini OAuth credentials, Git changes, or runtime media
unless --purge-runtime is explicitly supplied. Runtime data is archived before removal.
EOF
}

APPLY=false
PURGE_RUNTIME=false

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=true ;;
    --purge-runtime) PURGE_RUNTIME=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; usage; exit 2 ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
  echo "ERROR: run this inside the OpenShorts Git repository." >&2
  exit 1
fi

cd "$REPO_ROOT"

REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
if [[ "$REMOTE_URL" != *"adith92/openshorts"* ]]; then
  echo "ERROR: origin is not adith92/openshorts: $REMOTE_URL" >&2
  exit 1
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
REPORT_DIR="$REPO_ROOT/.deploy/local-cleanup/$TIMESTAMP"
mkdir -p "$REPORT_DIR"

printf '%s\n' "$(git rev-parse HEAD)" > "$REPORT_DIR/head-sha.txt"
git status --short > "$REPORT_DIR/git-status.txt"
git diff > "$REPORT_DIR/tracked-changes.patch"
git ls-files --others --exclude-standard > "$REPORT_DIR/untracked-files.txt"

GENERATED_PATHS=(
  ".venv"
  "venv"
  ".pytest_cache"
  ".mypy_cache"
  ".ruff_cache"
  "dashboard/node_modules"
  "dashboard/dist"
  "render-service/node_modules"
  "render-service/dist"
  "remotion/node_modules"
)

RUNTIME_PATHS=(
  "uploads"
  "downloads"
  "videos"
  "output"
)

echo "Repository : $REPO_ROOT"
echo "Branch     : $(git branch --show-current)"
echo "Commit     : $(git rev-parse --short=12 HEAD)"
echo "Backup     : $REPORT_DIR"
echo

echo "Generated artifacts selected for cleanup:"
for path in "${GENERATED_PATHS[@]}"; do
  if [[ -e "$path" ]]; then
    du -sh "$path" 2>/dev/null || printf 'present\t%s\n' "$path"
  fi
done

find . -type d -name __pycache__ -prune -print > "$REPORT_DIR/python-cache-directories.txt"
find . -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.log' \) -print > "$REPORT_DIR/generated-files.txt"

echo
echo "Protected paths that are never deleted by the normal cleanup:"
echo "  .env and .env.*"
echo "  .gemini and OAuth credentials"
echo "  tracked or untracked source files"
echo "  uploads/downloads/videos/output"

if [[ "$APPLY" != true ]]; then
  echo
  echo "DRY RUN COMPLETE. Re-run with --apply after reviewing $REPORT_DIR"
  exit 0
fi

for path in "${GENERATED_PATHS[@]}"; do
  if [[ -e "$path" ]]; then
    rm -rf -- "$path"
  fi
done

while IFS= read -r cache_dir; do
  [[ -n "$cache_dir" ]] && rm -rf -- "$cache_dir"
done < "$REPORT_DIR/python-cache-directories.txt"

while IFS= read -r generated_file; do
  [[ -n "$generated_file" ]] && rm -f -- "$generated_file"
done < "$REPORT_DIR/generated-files.txt"

if [[ "$PURGE_RUNTIME" == true ]]; then
  ARCHIVE_DIR="$REPORT_DIR/runtime-archive"
  mkdir -p "$ARCHIVE_DIR"

  for path in "${RUNTIME_PATHS[@]}"; do
    if [[ -e "$path" ]]; then
      mv -- "$path" "$ARCHIVE_DIR/"
    fi
  done

  echo "Runtime data moved to: $ARCHIVE_DIR"
fi

echo

echo "Cleanup complete. Remaining Git state:"
git status --short

echo

echo "Next validation commands:"
echo "  python3.11 -m venv .venv"
echo "  . .venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  python -m unittest tests/test_custom_ai_client.py tests/test_gemini_cli_oauth_client.py -v"
echo "  npm --prefix dashboard ci && npm --prefix dashboard run build"
echo "  npm --prefix render-service ci && npm --prefix render-service run build"
echo "  npm --prefix remotion ci"

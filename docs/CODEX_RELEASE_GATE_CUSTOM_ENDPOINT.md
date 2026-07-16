# Codex Release Gate: Custom Endpoint Model Auto-Fetch

## Objective

Review, fast-test, security-audit, and merge PR #4 from the user's local `adith92/openshorts` checkout only when every blocking gate passes.

Do not merely describe commands. Execute the checks, preserve the user's working tree, make a grounded release decision, and merge only when approved.

## Locked source

```text
Repository: adith92/openshorts
Pull request: #4
Base branch: main
Feature branch: feat/custom-endpoint-model-autofetch
Expected source SHA before this document commit: 935c405239eb8646949d0eeb1a603775bb889c9c
Merge strategy: fast-forward only, or GitHub merge/rebase only when the reviewed head SHA is unchanged
```

At execution time, fetch PR #4 and record its current exact head SHA. Use that SHA as the lock for the entire review. Stop if the head changes during review.

## Authorization

The repository owner authorizes Codex to:

1. Fetch PR #4 and its complete diff.
2. Create a temporary Git worktree.
3. Run local fast tests, builds, audits, and optional real-endpoint smoke tests.
4. Post the grounded review result to PR #4.
5. Mark the PR ready when all gates pass.
6. Merge PR #4 into `main` when all blocking checks pass.
7. Verify the resulting remote `main` SHA.

This does not authorize AWS deployment, VPS modification, secret rotation, or committing real credentials.

## Non-negotiable safety rules

- Preserve the user's original checkout, staged files, unstaged files, and untracked files.
- Perform review and builds in a temporary Git worktree.
- Never use `git reset --hard` in the user's checkout.
- Never use `git clean -fd`, `git clean -fdx`, force push, or `--force-with-lease`.
- Never print or commit endpoint API keys.
- Never add unrelated refactors.
- Never merge with failed or pending blocking checks.
- Never silently review a different SHA from the one recorded at the start.
- Keep the feature branch after merge unless the user explicitly asks to delete it.

## Phase 1: Protect the local checkout

```bash
ORIGINAL_ROOT="$(git rev-parse --show-toplevel)"
cd "$ORIGINAL_ROOT"

ORIGIN_URL="$(git remote get-url origin)"
case "$ORIGIN_URL" in
  https://github.com/adith92/openshorts.git|git@github.com:adith92/openshorts.git) ;;
  *) echo "BLOCKER: unexpected origin $ORIGIN_URL"; exit 1 ;;
esac

ORIGINAL_BRANCH="$(git branch --show-current || true)"
ORIGINAL_HEAD="$(git rev-parse HEAD)"
ORIGINAL_STATUS="$(git status --porcelain=v1)"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
REPORT_DIR="$ORIGINAL_ROOT/.deploy/codex-custom-endpoint/$TIMESTAMP"
mkdir -p "$REPORT_DIR"
printf '%s\n' "$ORIGINAL_BRANCH" > "$REPORT_DIR/original-branch.txt"
printf '%s\n' "$ORIGINAL_HEAD" > "$REPORT_DIR/original-head.txt"
printf '%s\n' "$ORIGINAL_STATUS" > "$REPORT_DIR/original-status.txt"
```

Do not require the original checkout to be clean because review must happen in a separate worktree.

## Phase 2: Fetch and lock PR #4

```bash
git fetch --prune origin main feat/custom-endpoint-model-autofetch

gh pr view 4 \
  --repo adith92/openshorts \
  --json number,state,isDraft,mergeable,baseRefName,headRefName,headRefOid,statusCheckRollup \
  > "$REPORT_DIR/pr-before.json"

BASE_SHA="$(git rev-parse origin/main)"
REVIEW_SHA="$(git rev-parse origin/feat/custom-endpoint-model-autofetch)"

printf 'Base: %s\nHead: %s\n' "$BASE_SHA" "$REVIEW_SHA" \
  | tee "$REPORT_DIR/locked-shas.txt"

gh pr checks 4 --repo adith92/openshorts \
  | tee "$REPORT_DIR/github-checks-before.txt"
```

Blocking requirements:

- PR #4 is open.
- Base branch is `main`.
- Head branch is `feat/custom-endpoint-model-autofetch`.
- GitHub's head OID equals `REVIEW_SHA`.
- Required checks are successful.
- PR is mergeable or potentially mergeable.

## Phase 3: Create an isolated worktree

```bash
WORKTREE="$(mktemp -d "${TMPDIR:-/tmp}/openshorts-custom-endpoint.XXXXXX")"
git worktree add --detach "$WORKTREE" "$REVIEW_SHA"
cd "$WORKTREE"

test "$(git rev-parse HEAD)" = "$REVIEW_SHA"
test -z "$(git status --porcelain=v1)"
```

Capture the review surface:

```bash
git diff --stat origin/main...HEAD | tee "$REPORT_DIR/diff-stat.txt"
git diff --name-status origin/main...HEAD | tee "$REPORT_DIR/changed-files.txt"
git log --oneline origin/main..HEAD | tee "$REPORT_DIR/commits.txt"
git diff --find-renames origin/main...HEAD > "$REPORT_DIR/full-review.diff"
```

## Phase 4: Required code review

Review the full diff, especially:

```text
dashboard/src/components/AIProviderSettings.jsx
custom_ai_client.py
sitecustomize.py
tests/test_custom_ai_client.py
tests/test_custom_endpoint_migration.py
tests/test_native_aws_deployment.py
.github/workflows/native-ci.yml
deploy/aws-native/custom-endpoint-check.sh
deploy/aws-native/openshorts.env.example
CUSTOM_AI_ENDPOINT.md
MIGRATION_CUSTOM_ENDPOINT.md
```

Evaluate:

- URL normalization correctness;
- model-list response parsing;
- Gemini-first sorting;
- selected-model propagation;
- API-key redaction;
- timeout and network-error behavior;
- CORS fallback behavior;
- browser storage disclosure;
- regressions to direct Gemini API-key mode;
- regressions to OpenAI-compatible generation;
- removal of deprecated Gemini CLI OAuth runtime;
- shell safety and AWS native configuration;
- generated or secret files accidentally tracked.

Write findings to:

```text
$REPORT_DIR/AUDIT_FINDINGS.md
```

Use severities:

```text
BLOCKER
HIGH
MEDIUM
LOW
INFO
```

Any unresolved `BLOCKER` or `HIGH` finding blocks merge.

## Phase 5: Functional acceptance criteria

Confirm all items:

- [ ] Custom Endpoint + API Key is the default provider for a fresh configuration.
- [ ] The dashboard derives `BASE_URL/models` correctly.
- [ ] Discovery uses `Authorization: Bearer API_KEY`.
- [ ] Discovery supports `data`, `models`, `result.data`, `result.models`, arrays of strings, and objects using `id`, `name`, `model`, or `slug`.
- [ ] IDs containing `gemini` are prioritized.
- [ ] The exact selected model ID is sent to `POST BASE_URL/chat/completions`.
- [ ] The user can reveal all endpoint models.
- [ ] Manual model-ID fallback remains available when discovery or CORS fails.
- [ ] API keys are redacted from displayed and raised errors.
- [ ] Direct Google Gemini API Key remains available for Files API and direct video upload workflows.
- [ ] Old `gemini_cli_oauth` browser settings migrate to a blank custom-endpoint form.
- [ ] Deprecated Gemini CLI OAuth runtime files, scripts, variables, tests, and active docs are removed.

## Phase 6: Git and structure audit

```bash
git diff --check origin/main...HEAD \
  | tee "$REPORT_DIR/diff-check.txt"
```

Search for stale runtime markers:

```bash
{
  git grep -n -i \
    -e 'gemini_cli_oauth_client' \
    -e 'OPENSHORTS_SERVER_GEMINI_OAUTH' \
    -e 'GEMINI_CLI_BINARY' \
    -e 'gemini-oauth-login.sh' \
    -e 'gemini-oauth-check.sh' \
    -- . || true
} | tee "$REPORT_DIR/stale-oauth-search.txt"
```

Historical migration documentation may mention removed names to explain migration. Active runtime source, environment templates, deployment scripts, and current operating instructions must not require Gemini CLI OAuth.

Confirm removed paths do not exist:

```bash
for path in \
  gemini_cli_oauth_client.py \
  GEMINI_CLI_OAUTH.md \
  tests/test_gemini_cli_oauth_client.py \
  deploy/aws-native/gemini-oauth-login.sh \
  deploy/aws-native/gemini-oauth-check.sh
do
  test ! -e "$path" || {
    echo "BLOCKER: deprecated path still exists: $path"
    exit 1
  }
done
```

## Phase 7: Secret and security audit

Never display complete suspected secrets.

```bash
{
  git grep -n -I -E \
    'AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[0-9A-Za-z]{20,}' \
    -- . || true
} > "$REPORT_DIR/secret-pattern-results.txt"

{
  git diff -U0 origin/main...HEAD \
    | grep -E '^\+' \
    | grep -Ei 'access[_-]?token|refresh[_-]?token|client[_-]?secret|private[_-]?key|aws_secret_access_key|api[_-]?key' \
    || true
} > "$REPORT_DIR/secret-keyword-results.txt"
```

Manually review matches. Examples and variable names can be legitimate. Real credentials are blocking.

Confirm:

- Base URLs reject embedded username/password credentials.
- Query strings and fragments are rejected by server configuration parsing.
- Invalid protocols and newline injection are rejected.
- API keys are not inserted into errors, logs, reports, docs, or screenshots.
- External production endpoints require HTTPS unless localhost/private network.
- Browser storage of endpoint configuration is explicitly administrator-only.
- Multi-user public deployment risk is documented.

## Phase 8: Fast Python test gate

```bash
python3 -m venv .codex-fast-venv
. .codex-fast-venv/bin/activate
python -m pip install --upgrade pip httpx

python -m py_compile \
  custom_ai_client.py \
  sitecustomize.py \
  app.py

python -m unittest \
  tests/test_custom_ai_client.py \
  tests/test_custom_endpoint_migration.py \
  tests/test_native_aws_deployment.py \
  -v \
  | tee "$REPORT_DIR/python-tests.txt"

deactivate
```

Any failure is blocking.

## Phase 9: Native shell validation

```bash
bash -n deploy/aws-native/custom-endpoint-check.sh
bash -n deploy/aws-native/prepare-host-layout.sh
bash -n scripts/clean-local-native.sh
```

Use `shellcheck` when installed. Treat correctness or security findings as blocking; stylistic warnings can be documented.

## Phase 10: Frontend build

```bash
npm --prefix dashboard ci
npm --prefix dashboard run build \
  | tee "$REPORT_DIR/frontend-build.txt"
test -f dashboard/dist/index.html
```

Review UI behavior after build, not only the exit code.

## Phase 11: Renderer build

```bash
npm --prefix render-service ci
npm --prefix remotion ci --no-audit --no-fund
npm --prefix render-service run build \
  | tee "$REPORT_DIR/renderer-build.txt"
test -f render-service/dist/server.js
```

Confirm builds did not modify tracked files:

```bash
if [[ -n "$(git status --porcelain=v1 --untracked-files=no)" ]]; then
  echo 'BLOCKER: tests or builds modified tracked files'
  git status --short
  exit 1
fi
```

## Phase 12: Optional real endpoint smoke test

Run only when credentials are provided locally. Never paste them into GitHub, reports, screenshots, or shell history that is being recorded.

Prefer a temporary protected environment file:

```bash
ENDPOINT_ENV="$(mktemp)"
chmod 600 "$ENDPOINT_ENV"
cat > "$ENDPOINT_ENV" <<'EOF'
AI_BASE_URL=https://endpoint.example.com/v1
AI_API_KEY=replace-locally
AI_MODEL=model-id-returned-by-models
EOF
```

Load it without printing values:

```bash
set -a
. "$ENDPOINT_ENV"
set +a

sudo --preserve-env=AI_BASE_URL,AI_API_KEY,AI_MODEL \
  bash deploy/aws-native/custom-endpoint-check.sh

rm -f "$ENDPOINT_ENV"
unset AI_BASE_URL AI_API_KEY AI_MODEL
```

Expected:

1. `GET /models` succeeds.
2. The selected model exists in the fetched list.
3. `POST /chat/completions` returns exactly `OPENSHORTS_OK`.
4. The API key is never printed.

When credentials are unavailable, report:

```text
Real endpoint smoke test: not run, credentials unavailable
```

Mock/unit coverage and green CI can approve the source merge, but a real endpoint smoke test remains required before AWS production traffic.

## Phase 13: Release report

Create:

```text
$REPORT_DIR/FINAL_REPORT.md
```

Required structure:

```markdown
# OpenShorts Custom Endpoint Release Review

- PR
- Base SHA
- Reviewed head SHA
- Timestamp
- Original working tree preserved

## Tests
- Git diff check
- Python compile
- Python unit tests
- Shell syntax
- Frontend build
- Renderer build
- GitHub CI
- Real endpoint smoke test

## Security Audit
- URL validation
- API-key redaction
- Secret scan
- Browser storage disclosure
- Deprecated OAuth removal
- Native AWS configuration

## Findings
- Blocker
- High
- Medium
- Low
- Info

## Decision
- MERGE APPROVED
or
- MERGE BLOCKED
```

Approve only when there are no unresolved `BLOCKER` or `HIGH` findings and all blocking tests pass.

## Phase 14: Race-condition check

Return to the original repository only to fetch refs. Do not alter its checkout.

```bash
cd "$ORIGINAL_ROOT"
git fetch --prune origin main feat/custom-endpoint-model-autofetch

FINAL_BASE_SHA="$(git rev-parse origin/main)"
FINAL_HEAD_SHA="$(git rev-parse origin/feat/custom-endpoint-model-autofetch)"

test "$FINAL_BASE_SHA" = "$BASE_SHA"
test "$FINAL_HEAD_SHA" = "$REVIEW_SHA"

gh pr checks 4 --repo adith92/openshorts \
  | tee "$REPORT_DIR/github-checks-final.txt"
```

Stop when either branch moved during review.

## Phase 15: Merge

Only when the report says `MERGE APPROVED`:

1. Post `$REPORT_DIR/FINAL_REPORT.md` to PR #4.
2. Mark PR #4 ready for review when still draft.
3. Merge only the exact reviewed head SHA.

Preferred GitHub CLI command:

```bash
gh pr ready 4 --repo adith92/openshorts || true

gh pr merge 4 \
  --repo adith92/openshorts \
  --rebase \
  --delete-branch=false
```

If repository policy does not allow rebase merge, use the repository's allowed non-force method. Never merge a different head SHA.

Verify:

```bash
git fetch origin main
POST_MERGE_MAIN="$(git rev-parse origin/main)"
printf '%s\n' "$POST_MERGE_MAIN" > "$REPORT_DIR/main-after-merge.txt"

gh pr view 4 \
  --repo adith92/openshorts \
  --json state,mergedAt,mergeCommit,headRefOid \
  > "$REPORT_DIR/pr-after.json"
```

## Phase 16: Cleanup and preservation check

```bash
cd "$ORIGINAL_ROOT"
git worktree remove --force "$WORKTREE"
git worktree prune

CURRENT_BRANCH="$(git branch --show-current || true)"
CURRENT_HEAD="$(git rev-parse HEAD)"
CURRENT_STATUS="$(git status --porcelain=v1)"
```

Confirm the original branch, local HEAD, staged files, unstaged files, and untracked files remain unchanged. Do not pull merged `main` into the user's current checkout automatically.

## Required final response

Report:

1. Merged or blocked.
2. Exact reviewed head SHA.
3. Previous remote `main` SHA.
4. Resulting remote `main` SHA when merged.
5. GitHub CI result.
6. Local test summary.
7. Security findings.
8. Real endpoint smoke-test status.
9. Path to `$REPORT_DIR/FINAL_REPORT.md`.
10. Confirmation that the original local working tree was untouched.

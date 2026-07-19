# Codex Local Audit and AWS Deployment

This document defines the required execution flow for the next OpenShorts work session.

## Scope

Codex must work from the latest `origin/main` while preserving all uncommitted local work. The task is to test locally, identify and fix validated bugs, run a security review, and deploy to the native AWS EC2/VPS environment only after every gate passes.

## Hard Rules

- Do not commit directly to `main`.
- Use a dedicated `feat/`, `fix/`, `security/`, or `refactor/` branch.
- Do not discard, overwrite, reset, clean, stash, or amend user work without first preserving and reporting it.
- Do not print, commit, copy, or expose API keys, tokens, credentials, cookies, or protected environment values.
- Do not merge or deploy when CI fails or a BLOCKER/HIGH security finding remains.
- Docker and Vercel are not production deployment paths.
- Production deployment uses native AWS EC2/VPS, Nginx, systemd, FastAPI, React/Vite, Node.js, Remotion, and FFmpeg.

## Phase 1: Synchronize and Inspect

1. Record the current branch, HEAD SHA, working-tree status, remotes, and untracked files.
2. Fetch the latest remote references and inspect `origin/main`.
3. Preserve local changes before rebasing or switching branches.
4. Inspect current pull requests, issues, branches, recent commits, CI configuration, and deployment documentation.
5. Confirm that the custom OpenAI-compatible endpoint is the primary text AI provider and direct Gemini remains limited to Gemini-specific capabilities.

## Phase 2: Baseline Local Validation

Run the existing suite before modifying code:

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v

cd dashboard
npm ci
npm run lint
npm run build

cd ../render-service
npm ci
npm run build

cd ..
bash -n deploy/aws-native/*.sh
bash -n scripts/*.sh
```

Record every command, exit code, failure, warning, and skipped test.

## Phase 3: Bug and Security Audit

Audit the current codebase for at least:

- missing authentication and authorization;
- missing rate limiting and quota protection;
- browser-side production secrets;
- job ownership and access isolation;
- permissive CORS;
- SSRF through user-controlled URLs, redirects, private IPs, localhost, link-local addresses, and cloud metadata endpoints;
- full-file reads that can exhaust VPS memory;
- unsafe filenames, extensions, MIME types, file sizes, and durations;
- command injection and unsafe subprocess usage;
- path traversal;
- unauthenticated static output exposure;
- in-memory job state and restart data loss;
- queue concurrency and race conditions;
- leaked secrets in logs or errors;
- incorrect requirement of Upload-Post credentials during non-publishing workflows;
- stale Docker, Vercel, Gemini CLI OAuth, or client-side encryption documentation.

Prioritize findings as BLOCKER, HIGH, MEDIUM, or LOW. Fix BLOCKER and HIGH findings before deployment. Add regression tests for every fix.

## Phase 4: Implementation

1. Create a dedicated branch from the latest `origin/main`.
2. Make small, reviewable commits with English commit messages.
3. Add tests before or with each fix.
4. Update documentation and environment examples when behavior changes.
5. Never add a production secret to Git.

## Phase 5: Release Gate

Repeat the complete validation suite after changes. Then inspect the full diff and run a final security review.

Deployment is blocked unless:

- all local tests and builds pass;
- GitHub CI passes on the exact reviewed SHA;
- no unresolved BLOCKER or HIGH finding exists;
- the branch is based on the latest `main`;
- a rollback commit or release point is recorded;
- persistent data affected by deployment is backed up;
- production environment values are verified without printing them.

## Phase 6: Native AWS Deployment

Follow `deploy/aws-native/README.md` and the systemd/Nginx files already in the repository.

Before changing production:

```bash
git rev-parse HEAD
git status --short
sudo systemctl status openshorts-backend --no-pager
sudo systemctl status openshorts-renderer --no-pager
sudo nginx -t
```

Create a rollback point and back up affected configuration and persistent runtime data. Deploy the exact reviewed SHA. Restart only the services affected by the change.

Example service validation:

```bash
sudo systemctl daemon-reload
sudo systemctl restart openshorts-backend
sudo systemctl restart openshorts-renderer
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status openshorts-backend --no-pager
sudo systemctl status openshorts-renderer --no-pager
sudo journalctl -u openshorts-backend -n 100 --no-pager
sudo journalctl -u openshorts-renderer -n 100 --no-pager
```

Adapt commands to the actual service names and repository deployment documentation. Do not guess production paths or overwrite unknown configuration.

## Phase 7: Post-Deployment Smoke Test

Verify:

- frontend loads through Nginx;
- FastAPI and renderer are healthy;
- services bind only to intended interfaces;
- no secret is visible in browser responses or logs;
- upload works without loading a large video entirely into memory;
- transcription completes;
- AI viral-moment analysis completes through the configured provider;
- clip extraction and rendering complete;
- subtitles are generated and applied;
- output can be downloaded;
- publishing remains optional and requires Upload-Post credentials only when invoked;
- one real end-to-end clipping job succeeds.

If a smoke test fails, stop, capture diagnostics, and roll back rather than continuing with a partially broken production release.

## Required Final Report

Return a concise report containing:

- branch and exact commit SHA deployed;
- files changed;
- bugs found and severity;
- fixes applied;
- tests/builds run and results;
- CI result;
- security review result;
- AWS deployment actions;
- service and smoke-test results;
- rollback point;
- remaining risks and unfinished work.

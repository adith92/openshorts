# AGENTS.md

## Repository Mission

OpenShorts turns long-form videos into Shorts, Reels, and TikTok clips, supports AI UGC generation, and provides YouTube metadata, thumbnail, and publishing workflows.

## Source of Truth

- Repository: `adith92/openshorts`
- Base all new work on the latest `main`.
- Production runs natively on AWS EC2/VPS.
- Docker and Vercel are not production paths.
- Use an OpenAI-compatible custom endpoint for primary text AI tasks.
- Use direct Gemini API only for Gemini Files API, direct video upload, image generation, and Gemini-specific tools.

## Branch and Pull Request Rules

- Never commit directly to `main`.
- Use `feat/`, `fix/`, `security/`, or `refactor/` branches.
- Preserve uncommitted local work before syncing, switching branches, rebasing, or cleaning.
- Every change requires tests, relevant documentation, and a security review.
- Do not merge when CI fails or a BLOCKER/HIGH security finding remains.
- Do not commit or display production secrets.

## Mandatory Work Order

1. Inspect repository, PRs, issues, branches, recent commits, CI, and relevant documentation.
2. Record the local branch, commit SHA, working-tree status, and untracked files.
3. Synchronize safely with `origin/main` without losing user work.
4. Run baseline tests and builds before editing.
5. Audit for bugs, regressions, security issues, memory pressure, concurrency failures, and deployment risk.
6. Fix validated findings and add regression tests.
7. Run the complete test/build/security gate again.
8. Open or update a PR and wait for green CI on the exact reviewed SHA.
9. Deploy to native AWS only after all gates pass.
10. Run service health checks and one real end-to-end clipping smoke test.

## Current Priorities

1. Authentication and authorization
2. Rate limiting and quota protection
3. Server-side production secrets
4. Job ownership and isolation
5. Restrictive CORS
6. SSRF protection
7. Streaming large video uploads and publishing
8. Persistent database and durable job queue
9. Upload-Post key required only during publishing
10. Accurate `CLAUDE.md`, `AGENTS.md`, and deployment documentation

## Validation Gate

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

Use scope-specific tests in addition to this baseline. Never put real API keys into commands, fixtures, logs, screenshots, PRs, or commits.

## Deployment Gate

Follow `deploy/aws-native/README.md`. Before deployment, record the exact reviewed SHA, create a rollback point, back up affected persistent data/configuration, and verify protected environment values without printing them.

After deployment, verify systemd, Nginx, backend, renderer, storage permissions, logs, upload, transcription, AI analysis, rendering, subtitles, output download, and one real clipping job.

## Required Report

Report in Bahasa Indonesia:

- files changed;
- tests/builds run and results;
- bugs found and severity;
- security review result;
- deployed SHA and AWS actions, when applicable;
- smoke-test result;
- rollback point;
- remaining risks and unfinished work.

Keep code and commit messages in English.

# CLAUDE.md

This file provides repository guidance for Claude Code and other coding agents working on OpenShorts.

## Source of Truth

- Repository: `adith92/openshorts`
- Primary branch: `main`
- Production path: native AWS EC2/VPS
- Docker and Vercel are not production deployment paths.
- Never commit directly to `main`. Use `feat/`, `fix/`, `security/`, or `refactor/` branches and open a pull request.

Before changing code, inspect the latest repository state, open pull requests, branches, recent commits, CI results, and related documentation.

## Product Scope

OpenShorts is an AI video platform for:

- clipping long videos into Shorts, Reels, and TikTok videos;
- AI UGC video generation;
- YouTube title, thumbnail, description, and publishing workflows.

## Production Architecture

- FastAPI backend
- React and Vite dashboard
- Node.js Remotion render service
- FFmpeg video processing
- Nginx reverse proxy
- systemd services
- persistent runtime storage under `/var/lib/openshorts`
- AWS EC2/VPS native deployment

The primary text-generation provider is an OpenAI-compatible custom endpoint. Direct Gemini API access remains available for Gemini Files API, direct video upload, image generation, and Gemini-specific tools.

## Required Execution Order

For every implementation or release task:

1. Synchronize the local checkout with the latest `origin/main` without discarding uncommitted user work.
2. Inspect the relevant code, tests, deployment configuration, and documentation.
3. Run the existing local test and build suite before modifying code.
4. Search for correctness, security, reliability, memory, concurrency, and deployment bugs.
5. Fix validated findings on a dedicated branch.
6. Add or update tests for every bug fix.
7. Update documentation when behavior, configuration, or deployment changes.
8. Run the complete validation gate again.
9. Perform a security review. Do not continue when a BLOCKER or HIGH finding remains.
10. Open or update a pull request. Never merge when CI fails.
11. Deploy to AWS only after local validation and CI are green.
12. Run post-deployment health checks and a real clipping smoke test.

## Current Security Priorities

1. Authentication and authorization
2. Rate limiting and quota protection
3. Move production API keys from browser storage to authenticated server-side storage
4. Job ownership and access isolation
5. Restrictive production CORS
6. SSRF protection for every user-controlled URL
7. Streaming file uploads and publishing instead of loading full videos into RAM
8. File type, size, duration, and filename validation
9. Persistent database and durable job queue
10. Upload-Post credentials required only when publishing

## Local Validation

Run the commands that apply to the changed scope. At minimum, validate all currently supported components:

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
```

Also validate native deployment scripts:

```bash
bash -n deploy/aws-native/*.sh
bash -n scripts/*.sh
```

Do not use real production API keys in tests, commands, logs, screenshots, fixtures, pull requests, or commits.

## AWS Deployment Gate

Deployment is allowed only when:

- the branch is based on the latest `main`;
- local tests and builds pass;
- GitHub CI passes;
- no unresolved BLOCKER or HIGH security finding exists;
- required environment variables are present in the protected server environment;
- a rollback point is recorded;
- persistent runtime directories are backed up when relevant.

Use the native deployment documentation under `deploy/aws-native/`. Do not introduce Docker or Vercel as a production path.

After deployment, verify:

- backend and renderer systemd services are active;
- Nginx configuration is valid and reloaded;
- backend and renderer bind only to their intended interfaces;
- application health endpoints respond;
- upload, transcription, AI analysis, rendering, subtitle generation, and output download work;
- logs contain no secrets or repeated errors;
- one real end-to-end clipping smoke test completes successfully.

## Completion Report

Every completed task must report:

- files changed;
- tests and builds executed;
- results;
- security review result;
- deployment actions and health-check results, when deployment occurred;
- remaining risks and follow-up work.

Use Bahasa Indonesia for user-facing explanations. Keep code, identifiers, documentation commands, branch names, and commit messages in English.

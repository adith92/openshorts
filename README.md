# OpenShorts

OpenShorts is a self-hosted AI video platform for turning long-form video into short clips, generating AI-assisted UGC videos, and preparing YouTube assets.

This fork targets a **native AWS deployment** using Linux services. Docker and Vercel are not part of the supported deployment path.

## Main features

### Clip Generator

- transcript-based viral moment detection;
- automatic short clip extraction;
- 9:16 reframing and subject tracking;
- subtitle generation and burn-in;
- hook overlays and AI-assisted video effects;
- optional translation and dubbing;
- generated clips served locally and optionally backed up to S3.

### AI Shorts

- product or website analysis;
- script generation;
- AI actor and voice workflows;
- B-roll generation;
- FFmpeg-based composition;
- optional publishing integrations.

### YouTube Studio

- title suggestions;
- thumbnail generation;
- description generation;
- chapter timestamp support;
- optional publishing integration.

## Architecture

```text
Internet
  |
  v
Nginx :80/:443
  |
  +-- React/Vite static frontend
  +-- FastAPI backend       127.0.0.1:8000
  +-- Remotion renderer     127.0.0.1:3100
  +-- local uploads/output  /var/lib/openshorts
  +-- AWS S3 via EC2 IAM instance role
  +-- Gemini CLI OAuth      /var/lib/openshorts/.gemini
```

Production services are managed by `systemd` and run as the dedicated Linux user `openshorts`.

## Repository layout

```text
.
├── app.py                         FastAPI API and job queue
├── main.py                        clipping pipeline
├── custom_ai_client.py            OpenAI-compatible provider
├── gemini_cli_oauth_client.py     Gemini CLI OAuth provider
├── sitecustomize.py               provider compatibility hook
├── s3_uploader.py                 S3 backup and gallery integration
├── dashboard/                     React/Vite frontend
├── render-service/                Node.js Remotion render API
├── remotion/                      Remotion compositions
├── tests/                         provider tests
├── CUSTOM_AI_ENDPOINT.md          custom endpoint guide
└── GEMINI_CLI_OAUTH.md            native OAuth guide
```

## Requirements

Recommended production host:

- Ubuntu Server LTS;
- Python 3.11;
- Node.js 22 LTS;
- FFmpeg;
- Nginx;
- Chromium or the browser runtime required by the installed Remotion version;
- at least 16 GiB RAM for the initial CPU deployment;
- encrypted EBS storage with sufficient free space;
- AWS Systems Manager Session Manager access;
- EC2 IAM instance role for S3 access.

The ML and video dependencies are substantial. Avoid very small EC2 instance types and undersized root volumes.

## Native local development

### Backend

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
npm --prefix dashboard ci
npm --prefix dashboard run dev
```

The Vite development server proxies API and media paths to the local backend and renderer.

### Renderer

```bash
npm --prefix render-service ci
npm --prefix remotion ci
npm --prefix render-service run build

PORT=3100 \
OUTPUT_DIR="$PWD/output" \
REMOTION_BUNDLE_PATH="$PWD/remotion" \
node render-service/dist/server.js
```

### Production frontend build

```bash
npm --prefix dashboard ci
npm --prefix dashboard run build
```

Serve `dashboard/dist` through Nginx.

## AI providers

OpenShorts supports three provider modes for transcript-based analysis.

### Google Gemini API key

Uses the regular Google GenAI client and supports Gemini-specific APIs required by direct file or video workflows.

### OpenAI-compatible endpoint

Supports internal or external gateways exposing `POST /chat/completions`.

See [CUSTOM_AI_ENDPOINT.md](CUSTOM_AI_ENDPOINT.md).

### Gemini CLI OAuth

Uses the official `@google/gemini-cli` package and its cached Google OAuth session.

This mode supports text-based analysis only. Direct Gemini Files API video uploads still require the regular Gemini API provider.

See [GEMINI_CLI_OAUTH.md](GEMINI_CLI_OAUTH.md).

## Native Gemini OAuth on AWS

Run the one-time login as the same Linux user that runs the backend:

```bash
sudo -u openshorts -H env \
  HOME=/var/lib/openshorts \
  NO_BROWSER=true \
  GOOGLE_GENAI_USE_GCA=true \
  GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true \
  GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli \
  /usr/local/bin/gemini
```

Verify it:

```bash
sudo -u openshorts -H env \
  HOME=/var/lib/openshorts \
  NO_BROWSER=true \
  GOOGLE_GENAI_USE_GCA=true \
  GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true \
  GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli \
  /usr/local/bin/gemini \
  -p "Reply with exactly OPENSHORTS_OK" \
  --output-format json \
  --approval-mode plan \
  --skip-trust
```

OAuth credentials remain managed by Gemini CLI under `/var/lib/openshorts/.gemini`. Never commit that directory.

## Environment variables

Example server-side values:

```dotenv
PYTHONUNBUFFERED=1
HOME=/var/lib/openshorts

UPLOAD_DIR=/var/lib/openshorts/uploads
OUTPUT_DIR=/var/lib/openshorts/output
MAX_CONCURRENT_JOBS=1

AWS_REGION=ap-southeast-3
AWS_S3_BUCKET=replace-private-bucket
AWS_S3_PUBLIC_BUCKET=replace-public-bucket

NO_BROWSER=true
GOOGLE_GENAI_USE_GCA=true
GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true
GEMINI_CLI_BINARY=/usr/local/bin/gemini
GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli

REMOTION_BUNDLE_PATH=/opt/openshorts/remotion
PORT=3100
```

Use an EC2 IAM instance role instead of storing permanent AWS access keys on the server.

Optional third-party keys entered through the UI include:

- Gemini API key;
- custom AI gateway key;
- fal.ai key;
- ElevenLabs key;
- Upload-Post key.

Never commit real keys.

## Tests

Provider tests:

```bash
python -m unittest \
  tests/test_custom_ai_client.py \
  tests/test_gemini_cli_oauth_client.py \
  -v
```

Frontend build:

```bash
npm --prefix dashboard ci
npm --prefix dashboard run build
```

Renderer build:

```bash
npm --prefix render-service ci
npm --prefix remotion ci
npm --prefix render-service run build
```

## Production checks

Internal services:

```bash
curl -fsS http://127.0.0.1:8000/api/config
curl -fsS http://127.0.0.1:3100/health
sudo ss -lntp
```

Expected binding:

```text
127.0.0.1:8000
127.0.0.1:3100
0.0.0.0:80
0.0.0.0:443
```

Ports 8000 and 3100 must not be publicly exposed.

## Security notes

- Run backend and renderer as `openshorts`, not root.
- Connect administratively through AWS Systems Manager where possible.
- Store generated media outside the Git checkout.
- Protect `/var/lib/openshorts/.gemini` with restrictive permissions.
- Use an EC2 IAM role for S3.
- Keep private clip storage blocked from public access.
- Public gallery objects should be read-only to the internet and writable only by the instance role.
- Keep `.env`, private keys, OAuth files, generated media, model weights, virtual environments, dependency folders, and build outputs out of Git.

## License

MIT License. See [LICENSE](LICENSE).

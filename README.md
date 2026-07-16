# OpenShorts

OpenShorts is a self-hosted AI video platform for turning long-form video into short clips, generating AI-assisted UGC videos, and preparing YouTube assets.

This fork targets a **native AWS EC2/VPS deployment** using Python, Node.js, Nginx, and `systemd`. Docker and Vercel are not part of the supported production path.

## Main features

### Clip Generator

- faster-whisper transcription with word-level timestamps;
- transcript-based viral moment detection;
- automatic short clip extraction;
- 9:16 reframing and subject tracking;
- subtitle generation and burn-in;
- hook overlays and AI-assisted video effects;
- generated media served locally and optionally backed up to S3.

### AI Shorts

- product or website analysis;
- script generation;
- AI actor, voice, and B-roll workflows;
- FFmpeg composition;
- optional social publishing integrations.

### YouTube Studio

- title suggestions;
- thumbnail generation;
- description and chapter generation;
- optional publishing integration.

## Production architecture

```text
Internet
  |
  v
Nginx :80/:443
  |
  +-- React/Vite static frontend
  +-- FastAPI backend       127.0.0.1:8000
  +-- Remotion renderer     127.0.0.1:3100
  +-- persistent runtime    /var/lib/openshorts
  +-- AWS S3 through EC2 IAM instance role
  +-- Gemini OAuth account  /var/lib/openshorts/.gemini
```

Production services run as the dedicated Linux account:

```text
openshorts
```

## Persistent Gemini OAuth on AWS

The preferred provider for transcript analysis is:

```text
Gemini OAuth — account stored on AWS server
```

The Google account is authenticated once through the official Gemini CLI. Access and refresh credentials remain on the VPS under:

```text
/var/lib/openshorts/.gemini
```

The browser stores only non-sensitive provider preferences such as model and timeout.

Enable server OAuth in the protected service environment:

```dotenv
HOME=/var/lib/openshorts
OPENSHORTS_SERVER_GEMINI_OAUTH=true
OPENSHORTS_GEMINI_MODEL=auto
OPENSHORTS_GEMINI_TIMEOUT_SECONDS=180
GEMINI_CLI_BINARY=/usr/local/bin/gemini
GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli
GEMINI_CLI_CREDENTIAL_DIR=/var/lib/openshorts/.gemini
NO_BROWSER=true
GOOGLE_GENAI_USE_GCA=true
GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true
```

Login once through AWS Systems Manager:

```bash
sudo bash deploy/aws-native/gemini-oauth-login.sh
```

Verify the stored account:

```bash
sudo bash deploy/aws-native/gemini-oauth-check.sh
```

See:

- [Native AWS deployment](deploy/aws-native/README.md)
- [Gemini OAuth security and operation](GEMINI_CLI_OAUTH.md)

### OAuth scope

Gemini CLI OAuth supports text-based operations such as transcript analysis, viral moment selection, hooks, titles, and descriptions.

The Gemini Files API is not exposed by Gemini CLI. Features that upload a video directly to Gemini still require the regular **Google Gemini API Key** provider.

## AI provider options

### Gemini OAuth on AWS server

- default option for transcript analysis;
- no Gemini key stored in the browser;
- account remains attached to the VPS;
- server binary and filesystem paths cannot be overridden by client requests.

### Google Gemini API key

Use this for Gemini-specific APIs, especially direct file and video upload workflows.

### OpenAI-compatible endpoint

Supports internal or external gateways exposing `POST /chat/completions`.

See [CUSTOM_AI_ENDPOINT.md](CUSTOM_AI_ENDPOINT.md).

## Repository layout

```text
.
├── app.py
├── main.py
├── custom_ai_client.py
├── gemini_cli_oauth_client.py
├── sitecustomize.py
├── s3_uploader.py
├── dashboard/
├── render-service/
├── remotion/
├── deploy/aws-native/
├── scripts/
└── tests/
```

## Native local development

### Backend

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

For local Gemini CLI OAuth testing, explicitly enable it and use a local credential directory:

```bash
export OPENSHORTS_SERVER_GEMINI_OAUTH=true
export HOME="$PWD/.local-openshorts-home"
export GEMINI_CLI_CREDENTIAL_DIR="$HOME/.gemini"
export GEMINI_CLI_WORKING_DIR="$HOME/tmp/gemini-cli"
```

Never commit that home directory.

### Frontend

```bash
npm --prefix dashboard ci
npm --prefix dashboard run dev
```

Production build:

```bash
npm --prefix dashboard ci
npm --prefix dashboard run build
```

Serve `dashboard/dist` through Nginx.

### Renderer

```bash
npm --prefix render-service ci
npm --prefix remotion install --no-audit --no-fund
npm --prefix render-service run build

PORT=3100 \
OUTPUT_DIR="$PWD/output" \
REMOTION_BUNDLE_PATH="$PWD/remotion" \
node render-service/dist/server.js
```

## AWS environment

Copy the native template:

```bash
sudo cp deploy/aws-native/openshorts.env.example \
  /etc/openshorts/openshorts.env
sudo chown root:openshorts /etc/openshorts/openshorts.env
sudo chmod 0640 /etc/openshorts/openshorts.env
```

Use an EC2 IAM instance role instead of storing permanent AWS access keys on the VPS.

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
npm --prefix remotion install --no-audit --no-fund
npm --prefix render-service run build
```

GitHub CI runs these gates on the active cleanup PR.

## Security notes

- Run backend and renderer as `openshorts`, never root.
- Use AWS Systems Manager for administrative access.
- Keep ports 8000 and 3100 bound to localhost.
- Persist `/var/lib/openshorts` on encrypted EBS.
- Protect `/var/lib/openshorts/.gemini` with mode `0700` and files with mode `0600`.
- Do not expose the application publicly without adding authentication and rate limiting.
- Use an EC2 IAM role for S3.
- Never commit `.env`, OAuth files, API keys, generated media, model weights, virtual environments, dependency folders, or build outputs.

## License

MIT License. See [LICENSE](LICENSE).

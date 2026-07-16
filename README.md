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
  +-- OpenAI-compatible custom AI endpoint
```

Production services run as the dedicated Linux account:

```text
openshorts
```

## Primary AI setup: Custom Endpoint + API Key

The default AI provider is an OpenAI-compatible endpoint.

In **Settings**:

1. Enter the Base URL.
2. Enter the endpoint API key.
3. OpenShorts automatically fetches `GET /models`.
4. Gemini model IDs are prioritized in the dropdown.
5. Select the desired Gemini model.
6. Save the endpoint.

For a Base URL such as:

```text
https://router.example.com/v1
```

OpenShorts uses:

```text
GET  https://router.example.com/v1/models
POST https://router.example.com/v1/chat/completions
```

The API key is sent using Bearer authentication. The selected model ID is passed unchanged to the chat-completions request.

The UI recognizes common model-list responses, including:

```json
{"data": [{"id": "google/gemini-2.5-flash"}]}
```

```json
{"models": [{"name": "models/gemini-2.5-pro"}]}
```

See [CUSTOM_AI_ENDPOINT.md](CUSTOM_AI_ENDPOINT.md) for the endpoint contract, CORS requirements, troubleshooting, and native AWS configuration.

### Model discovery and CORS

Automatic model discovery runs from the dashboard so the list updates immediately while Settings are edited.

An external endpoint must allow the OpenShorts web origin and these request headers:

```text
Authorization
Accept
```

When CORS blocks discovery, the Settings screen keeps a manual model-ID fallback. Generation still runs through the FastAPI backend after a valid model ID is saved.

### Direct Gemini API fallback

The regular Google Gemini API-key provider remains available for Gemini-specific operations that are not exposed by an OpenAI-compatible router, including direct Gemini Files API video uploads.

## Repository layout

```text
.
├── app.py
├── main.py
├── custom_ai_client.py
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

Optional server-side custom endpoint fallback:

```bash
export AI_PROVIDER=openai_compatible
export AI_BASE_URL=https://router.example.com/v1
export AI_API_KEY=replace_me
export AI_MODEL=google/gemini-2.5-flash
```

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
npm --prefix remotion ci --no-audit --no-fund
npm --prefix render-service run build

HOST=127.0.0.1 \
PORT=3100 \
OUTPUT_DIR="$PWD/output" \
REMOTION_BUNDLE_PATH="$PWD/remotion" \
node render-service/dist/server.js
```

## AWS environment

Prepare the native host layout:

```bash
sudo bash deploy/aws-native/prepare-host-layout.sh
```

Copy the service environment template:

```bash
sudo cp deploy/aws-native/openshorts.env.example \
  /etc/openshorts/openshorts.env
sudo chown root:openshorts /etc/openshorts/openshorts.env
sudo chmod 0640 /etc/openshorts/openshorts.env
```

Set at least:

```dotenv
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://router.example.com/v1
AI_API_KEY=replace_with_endpoint_api_key
AI_MODEL=google/gemini-2.5-flash
```

Use an EC2 IAM instance role instead of storing permanent AWS access keys on the VPS.

## Tests

Python provider and native deployment tests:

```bash
python -m unittest \
  tests/test_custom_ai_client.py \
  tests/test_native_aws_deployment.py \
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
npm --prefix remotion ci --no-audit --no-fund
npm --prefix render-service run build
```

GitHub CI runs these gates on the active pull request.

## Security notes

- Run backend and renderer as `openshorts`, never root.
- Use AWS Systems Manager for administrative access.
- Keep ports 8000 and 3100 bound to localhost.
- Persist `/var/lib/openshorts` on encrypted EBS.
- Protect `/etc/openshorts/openshorts.env` as `root:openshorts` with mode `0640`.
- Do not expose the application publicly without authentication and rate limiting.
- Use HTTPS for external AI endpoints.
- Use an EC2 IAM role for S3.
- Never commit `.env`, API keys, generated media, model weights, virtual environments, dependency folders, or build outputs.

## License

MIT License. See [LICENSE](LICENSE).

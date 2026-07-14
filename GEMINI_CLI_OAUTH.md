# Gemini CLI OAuth for OpenShorts

This branch adds a third AI provider for transcript-based automatic clipping:

- Google Gemini API Key
- OpenAI-compatible custom endpoint
- **Gemini CLI OAuth / Sign in with Google**

The OAuth implementation uses the official `@google/gemini-cli` package. OpenShorts invokes Gemini CLI in non-interactive JSON mode, while Gemini CLI manages Google OAuth credentials and refresh tokens.

## Why this design

OpenShorts does not copy, parse, or expose Gemini CLI refresh tokens. The official CLI owns the complete OAuth flow and stores its credentials in a persistent Docker volume.

The clipping flow is:

```text
OpenShorts transcript prompt
  -> official Gemini CLI
  -> cached Google OAuth session
  -> Gemini Code Assist backend
  -> structured JSON response
  -> OpenShorts clip generation
```

## Build

Checkout the feature branch and rebuild the backend image:

```bash
git fetch origin
git switch feat/custom-ai-endpoint
docker compose build --no-cache backend
docker compose up -d
```

Verify Gemini CLI is installed:

```bash
docker compose exec backend gemini --version
```

## One-time Google OAuth login

Run:

```bash
docker compose exec backend sh -lc 'NO_BROWSER=true gemini'
```

The CLI prints a URL and authorization code. Open the URL in your browser, sign in to Google, and complete the flow.

OAuth credentials are stored in the named volume:

```text
gemini-cli-data
```

They survive normal container rebuilds and restarts.

## Configure OpenShorts

1. Open **Settings**.
2. Choose **Gemini CLI OAuth / Sign in with Google**.
3. Set the model to `auto` unless a specific OAuth-supported model is required.
4. Click **Save AI**.
5. Run Clip Generator normally.

`auto` omits the Gemini CLI `--model` flag, allowing the CLI to select its current default model.

## Test OAuth inside Docker

```bash
docker compose exec backend sh -lc \
  'gemini -p "Reply with exactly OPENSHORTS_OK" --output-format json --approval-mode plan --skip-trust'
```

Expected output includes:

```json
{
  "response": "OPENSHORTS_OK"
}
```

## Security behavior

- No OAuth token is stored in the browser.
- No OAuth token is included in OpenShorts job metadata.
- Gemini CLI runs with `--approval-mode plan`.
- Gemini CLI uses a dedicated empty working directory.
- The OAuth volume should not be exposed to untrusted users.
- This mode is intended for local and private self-hosted deployments.

## Limitations

Gemini CLI OAuth currently covers text-based tasks such as:

- viral moment detection from transcripts
- timestamp selection
- hook text
- titles and descriptions

It does not expose the Gemini Files API used by features that directly upload video files to Gemini. Use the regular Gemini API provider for those operations.

## Reset OAuth

To remove only the stored Gemini CLI credentials:

```bash
docker compose down
docker volume rm openshorts_gemini-cli-data
```

The exact volume prefix may differ depending on the Compose project name. Check it with:

```bash
docker volume ls | grep gemini-cli-data
```

## Run tests

```bash
python -m unittest \
  tests/test_custom_ai_client.py \
  tests/test_gemini_cli_oauth_client.py \
  -v
```

# Gemini CLI OAuth for OpenShorts

This branch adds a third AI provider for transcript-based automatic clipping:

- Google Gemini API Key
- OpenAI-compatible custom endpoint
- **Gemini CLI OAuth / Sign in with Google**

The OAuth implementation uses the official `@google/gemini-cli` package. OpenShorts invokes Gemini CLI in non-interactive JSON mode, while Gemini CLI manages Google OAuth credentials and refresh tokens.

## Why this design

OpenShorts does not copy, parse, or expose Gemini CLI refresh tokens. The official CLI owns the complete OAuth flow and stores its credentials persistently.

The clipping flow is:

```text
OpenShorts transcript prompt
  -> official Gemini CLI
  -> cached Google OAuth session
  -> Gemini Code Assist backend
  -> structured JSON response
  -> OpenShorts clip generation
```

## Native AWS/Systemd Deployment (Primary)

In a native deployment, the Gemini CLI runs under the `openshorts` service user on the EC2 instance.

### One-time Google OAuth login

Run the following on the EC2 host:

```bash
sudo -u openshorts -H env \
  HOME=/var/lib/openshorts \
  NO_BROWSER=true \
  GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true \
  gemini
```

The CLI prints a URL and authorization code. Open the URL in your browser, sign in to Google, and complete the flow.
The OAuth credentials are stored in `/var/lib/openshorts/.gemini` and survive backend restarts.

### Configure OpenShorts

1. Open **Settings**.
2. Choose **Gemini CLI OAuth / Sign in with Google**.
3. Set the model to `auto` unless a specific OAuth-supported model is required.
4. Click **Save AI**.
5. Run Clip Generator normally.

### Test OAuth natively

```bash
sudo -u openshorts -H env \
  HOME=/var/lib/openshorts \
  NO_BROWSER=true \
  GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true \
  gemini \
  -p "Reply with exactly OPENSHORTS_OK" \
  --output-format json \
  --approval-mode plan \
  --skip-trust
```

## Docker Deployment (Legacy / Local)

If you are running the legacy Docker Compose environment locally, you can use `docker compose exec`.

### One-time Google OAuth login (Docker)

```bash
docker compose exec backend sh -lc 'NO_BROWSER=true gemini'
```

OAuth credentials are stored in the named volume `gemini-cli-data`.

### Test OAuth (Docker)

```bash
docker compose exec backend sh -lc \
  'gemini -p "Reply with exactly OPENSHORTS_OK" --output-format json --approval-mode plan --skip-trust'
```

### Reset OAuth (Docker)

```bash
docker compose down
docker volume rm openshorts_gemini-cli-data
```

## Limitations

Gemini CLI OAuth currently covers text-based tasks such as viral moment detection from transcripts.
It does not expose the Gemini Files API. Use the regular Gemini API provider for those operations.

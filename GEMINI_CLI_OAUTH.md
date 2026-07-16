# Gemini CLI OAuth for OpenShorts

OpenShorts can use the official `@google/gemini-cli` package for transcript-based AI tasks without storing a Gemini API key in the browser.

This repository targets a **native AWS deployment**. Docker is not required or supported by the deployment workflow documented here.

## Supported scope

Gemini CLI OAuth supports text-based operations such as:

- viral moment detection from transcripts;
- timestamp selection;
- hook text;
- titles and descriptions.

It does not expose the Gemini Files API. Features that upload a video directly to Gemini must continue using the regular Gemini API provider.

## Runtime identity

Install and run OpenShorts with a dedicated Linux service user:

```text
openshorts
```

The backend service and the one-time OAuth login must use the same user and home directory:

```text
HOME=/var/lib/openshorts
```

OAuth credentials are managed by Gemini CLI and stored under:

```text
/var/lib/openshorts/.gemini
```

Do not copy refresh tokens into the repository, application settings, environment files, or deployment logs.

## Install Gemini CLI

Install Node.js 22 LTS and the official CLI on the AWS host:

```bash
sudo npm install -g @google/gemini-cli@latest
command -v gemini
gemini --version
```

## One-time OAuth login on AWS

Connect to the instance through AWS Systems Manager Session Manager, then run:

```bash
sudo -u openshorts -H env \
  HOME=/var/lib/openshorts \
  NO_BROWSER=true \
  GOOGLE_GENAI_USE_GCA=true \
  GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true \
  GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli \
  /usr/local/bin/gemini
```

Open the URL shown by Gemini CLI in a local browser, complete Google sign-in, and return to the terminal.

Never perform this login as `root`, `ubuntu`, or another account. The systemd backend runs as `openshorts` and must be able to read the same credential store.

## Verify the OAuth session

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

Expected response:

```json
{
  "response": "OPENSHORTS_OK"
}
```

Restart and verify the backend after authentication:

```bash
sudo systemctl restart openshorts-backend
sudo systemctl --no-pager --full status openshorts-backend
```

## Configure OpenShorts

1. Open **Settings**.
2. Select **Gemini CLI OAuth / Sign in with Google**.
3. Keep the model set to `auto` unless a specific supported model is required.
4. Save the AI settings.
5. Run a transcript-based clipping analysis.

## Required systemd environment

The backend service should include:

```dotenv
HOME=/var/lib/openshorts
NO_BROWSER=true
GOOGLE_GENAI_USE_GCA=true
GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true
GEMINI_CLI_BINARY=/usr/local/bin/gemini
GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli
```

Protect the service environment file and credential directory:

```bash
sudo chown -R openshorts:openshorts /var/lib/openshorts/.gemini
sudo chmod 700 /var/lib/openshorts/.gemini
```

## Reset OAuth

Stop the backend before resetting credentials:

```bash
sudo systemctl stop openshorts-backend
sudo rm -rf /var/lib/openshorts/.gemini
sudo install -d -o openshorts -g openshorts -m 0700 /var/lib/openshorts/.gemini
```

Run the one-time login again, then start the backend:

```bash
sudo systemctl start openshorts-backend
```

## Tests

```bash
python -m unittest \
  tests/test_custom_ai_client.py \
  tests/test_gemini_cli_oauth_client.py \
  -v
```

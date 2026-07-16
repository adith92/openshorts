# Persistent Gemini OAuth on an AWS VPS

OpenShorts can use the official `@google/gemini-cli` package for transcript-based AI tasks without placing a Gemini API key or Google OAuth token in the browser.

The intended production setup is:

```text
Browser
  -> sends non-sensitive provider/model preferences
FastAPI on AWS VPS
  -> invokes official Gemini CLI
Gemini CLI
  -> reads the cached Google OAuth session owned by Linux user openshorts
```

## What is stored where

### AWS VPS

Gemini CLI owns and stores the Google OAuth session under:

```text
/var/lib/openshorts/.gemini
```

This directory must live on persistent encrypted EBS storage and be owned by:

```text
openshorts:openshorts
```

Recommended permissions:

```bash
sudo chown -R openshorts:openshorts /var/lib/openshorts/.gemini
sudo chmod 0700 /var/lib/openshorts/.gemini
sudo find /var/lib/openshorts/.gemini -type d -exec chmod 0700 {} +
sudo find /var/lib/openshorts/.gemini -type f -exec chmod 0600 {} +
```

### Browser

The browser stores only:

- provider name;
- model selection;
- request timeout.

It does not receive or store Google access tokens, refresh tokens, credential files, Gemini CLI paths, or the Linux home directory.

## Server opt-in

Server OAuth is disabled unless the protected service environment contains:

```dotenv
OPENSHORTS_SERVER_GEMINI_OAUTH=true
```

Use these settings in `/etc/openshorts/openshorts.env`:

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

The service environment file should be owned by `root:openshorts` with mode `0640`.

## Install Gemini CLI

Use Node.js 22 LTS, then install the official package:

```bash
sudo npm install -g @google/gemini-cli@latest
/usr/local/bin/gemini --version
```

## One-time Google login

Connect through AWS Systems Manager Session Manager and run:

```bash
sudo bash deploy/aws-native/gemini-oauth-login.sh
```

Equivalent manual command:

```bash
sudo -u openshorts -H env \
  HOME=/var/lib/openshorts \
  NO_BROWSER=true \
  GOOGLE_GENAI_USE_GCA=true \
  GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true \
  GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli \
  /usr/local/bin/gemini
```

Open the URL or device code shown by the CLI in a local browser and sign in with the Google account that should remain attached to this server.

Never log in as `root`, `ubuntu`, or another user. The backend runs as `openshorts` and must own the same credential store.

## Verify the stored session

```bash
sudo bash deploy/aws-native/gemini-oauth-check.sh
```

The checker sends a fixed harmless prompt and requires the response `OPENSHORTS_OK`. Raw CLI output is hidden to reduce the risk of authentication data appearing in logs.

Restart the backend after a successful login:

```bash
sudo systemctl restart openshorts-backend
sudo systemctl --no-pager --full status openshorts-backend
```

## Configure the frontend

1. Open **Settings**.
2. Choose **Gemini OAuth — account stored on AWS server**.
3. Keep model `auto` unless a specific OAuth-supported model is required.
4. Click **Use Server OAuth**.

No Gemini key is requested for this mode.

## Security behavior

- Server OAuth requires explicit administrator opt-in.
- Google credentials remain on the VPS.
- Browser configuration cannot override the Gemini binary.
- Browser configuration cannot override the Gemini working directory.
- Gemini CLI executes with `--approval-mode plan` and `--skip-trust`.
- Prompts are passed directly as command arguments to the official CLI.
- The backend returns only generated text, not credential data.
- Do not expose the VPS to untrusted users without adding application authentication and rate limiting.

## Supported scope

Gemini CLI OAuth supports text-based operations such as:

- transcript viral-moment analysis;
- timestamp selection;
- hook generation;
- titles and descriptions.

It does not expose the Gemini Files API. Features that directly upload video files to Gemini must use the regular **Google Gemini API Key** provider.

## Change the attached Google account

Stop the backend and archive the current credential directory:

```bash
sudo systemctl stop openshorts-backend
sudo mv /var/lib/openshorts/.gemini \
  "/var/lib/openshorts/.gemini.backup.$(date +%Y%m%d-%H%M%S)"
sudo install -d -o openshorts -g openshorts -m 0700 \
  /var/lib/openshorts/.gemini
```

Run the login and check scripts again, then start the backend:

```bash
sudo bash deploy/aws-native/gemini-oauth-login.sh
sudo bash deploy/aws-native/gemini-oauth-check.sh
sudo systemctl start openshorts-backend
```

Remove the backup only after the new account succeeds in a real clipping job.

## Tests

```bash
python -m unittest \
  tests/test_custom_ai_client.py \
  tests/test_gemini_cli_oauth_client.py \
  -v
```

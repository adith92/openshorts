# Native AWS Deployment

This directory contains the production settings for running OpenShorts directly on an AWS EC2 VPS without Docker.

## Runtime identity

Create one dedicated Linux account:

```bash
sudo useradd \
  --system \
  --create-home \
  --home-dir /var/lib/openshorts \
  --shell /bin/bash \
  openshorts
sudo passwd -l openshorts
```

Create persistent directories:

```bash
sudo install -d -o openshorts -g openshorts -m 0750 \
  /opt/openshorts \
  /var/lib/openshorts/uploads \
  /var/lib/openshorts/output

sudo install -d -o openshorts -g openshorts -m 0700 \
  /var/lib/openshorts/.gemini \
  /var/lib/openshorts/tmp/gemini-cli

sudo install -d -o root -g openshorts -m 0750 /etc/openshorts
```

The EC2 root volume should use encrypted persistent EBS storage. Do not place `/var/lib/openshorts` on ephemeral instance storage.

## Install Gemini CLI

Use Node.js 22 LTS:

```bash
node --version
sudo npm install -g @google/gemini-cli@latest
/usr/local/bin/gemini --version
```

## Environment

```bash
sudo cp deploy/aws-native/openshorts.env.example \
  /etc/openshorts/openshorts.env
sudo chown root:openshorts /etc/openshorts/openshorts.env
sudo chmod 0640 /etc/openshorts/openshorts.env
sudo editor /etc/openshorts/openshorts.env
```

Keep:

```dotenv
OPENSHORTS_SERVER_GEMINI_OAUTH=true
HOME=/var/lib/openshorts
GEMINI_CLI_CREDENTIAL_DIR=/var/lib/openshorts/.gemini
```

Do not add Google OAuth tokens or long-lived AWS access keys to the environment file.

## One-time Google OAuth login

Connect through AWS Systems Manager Session Manager, then run:

```bash
sudo bash deploy/aws-native/gemini-oauth-login.sh
```

The official Gemini CLI prints a URL or device code. Open it in your local browser and sign in with the Google account that should remain attached to this server.

Credentials are stored by Gemini CLI under:

```text
/var/lib/openshorts/.gemini
```

They survive application rebuilds, Git updates, service restarts, and EC2 reboots because the directory lives on persistent EBS.

Do not run the login as `root` or `ubuntu`. The backend service runs as `openshorts` and must own the same credential store.

## Verify OAuth

```bash
sudo bash deploy/aws-native/gemini-oauth-check.sh
```

Expected result:

```text
PASS: persistent Gemini OAuth is ready for the OpenShorts service user
```

The checker hides raw CLI output so authentication data cannot leak into terminal logs.

## Install systemd services

Adjust the Node binary in the renderer unit when `command -v node` does not return `/usr/bin/node`.

```bash
sudo cp deploy/aws-native/openshorts-backend.service \
  /etc/systemd/system/openshorts-backend.service
sudo cp deploy/aws-native/openshorts-renderer.service \
  /etc/systemd/system/openshorts-renderer.service

sudo systemctl daemon-reload
sudo systemctl enable openshorts-backend openshorts-renderer
sudo systemctl restart openshorts-renderer
sudo systemctl restart openshorts-backend
```

Check:

```bash
sudo systemctl --no-pager --full status openshorts-backend
sudo systemctl --no-pager --full status openshorts-renderer
sudo journalctl -u openshorts-backend -n 100 --no-pager
```

## Frontend setting

Choose:

```text
Gemini OAuth — account stored on AWS server
```

Then click:

```text
Use Server OAuth
```

The browser stores only a non-sensitive provider selection, model, and timeout. Google access and refresh credentials never leave the VPS.

## Security boundary

Client requests cannot select the server executable or working directory. These values are accepted only from the protected systemd environment:

```dotenv
GEMINI_CLI_BINARY=/usr/local/bin/gemini
GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli
```

The server feature is disabled unless this explicit opt-in exists:

```dotenv
OPENSHORTS_SERVER_GEMINI_OAUTH=true
```

## Scope limitation

Gemini CLI OAuth is used for text-based tasks such as transcript analysis, viral moment selection, hooks, titles, and descriptions.

The Gemini Files API is not exposed by Gemini CLI. Features that upload a video directly to Gemini still require the regular **Google Gemini API Key** provider.

## Reset or change the attached Google account

```bash
sudo systemctl stop openshorts-backend
sudo mv /var/lib/openshorts/.gemini \
  "/var/lib/openshorts/.gemini.backup.$(date +%Y%m%d-%H%M%S)"
sudo install -d -o openshorts -g openshorts -m 0700 \
  /var/lib/openshorts/.gemini
sudo bash deploy/aws-native/gemini-oauth-login.sh
sudo bash deploy/aws-native/gemini-oauth-check.sh
sudo systemctl start openshorts-backend
```

Keep the backup until the new account passes a real clipping test, then remove it securely.

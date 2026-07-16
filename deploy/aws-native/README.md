# Native AWS Deployment

This directory contains the production settings for running OpenShorts directly on an AWS EC2 VPS without Docker.

## Prepare the persistent host layout

After cloning the repository to `/opt/openshorts`, run:

```bash
sudo bash deploy/aws-native/prepare-host-layout.sh
```

The helper:

- creates the dedicated Linux account `openshorts` when needed;
- creates persistent runtime directories under `/var/lib/openshorts`;
- links `/opt/openshorts/uploads` and `/opt/openshorts/output` to persistent storage;
- archives non-empty legacy runtime directories instead of deleting them.

The resulting layout is:

```text
/opt/openshorts/uploads -> /var/lib/openshorts/uploads
/opt/openshorts/output  -> /var/lib/openshorts/output
```

The EC2 root volume should use encrypted persistent EBS storage. Do not place `/var/lib/openshorts` on ephemeral instance storage.

## Configure the custom AI endpoint

Copy the protected environment template:

```bash
sudo cp deploy/aws-native/openshorts.env.example \
  /etc/openshorts/openshorts.env
sudo chown root:openshorts /etc/openshorts/openshorts.env
sudo chmod 0640 /etc/openshorts/openshorts.env
sudo editor /etc/openshorts/openshorts.env
```

Set the endpoint values:

```dotenv
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://router.example.com/v1
AI_API_KEY=replace_with_endpoint_api_key
AI_MODEL=google/gemini-2.5-flash
AI_TEMPERATURE=0.2
AI_TIMEOUT_SECONDS=180
AI_MAX_TOKENS=4096
```

The Base URL is normalized so these forms are accepted:

```text
https://router.example.com/v1
https://router.example.com/v1/models
https://router.example.com/v1/chat/completions
```

OpenShorts uses the same API root for:

```text
GET  /models
POST /chat/completions
```

Do not commit the real API key. Do not put it in shell history, cloud-init user data, screenshots, or support logs.

## Verify the endpoint on the VPS

Run the model-list request as the same service user as the backend:

```bash
sudo -u openshorts -H bash -lc '
  set -a
  . /etc/openshorts/openshorts.env
  set +a
  curl --fail --silent --show-error \
    --header "Authorization: Bearer ${AI_API_KEY}" \
    --header "Accept: application/json" \
    "${AI_BASE_URL%/}/models" \
    | python3 -m json.tool \
    | head -80
'
```

Confirm that the response contains the Gemini model ID intended for production.

Test a small chat completion without printing the API key:

```bash
sudo -u openshorts -H bash -lc '
  set -a
  . /etc/openshorts/openshorts.env
  set +a
  curl --fail --silent --show-error \
    --header "Authorization: Bearer ${AI_API_KEY}" \
    --header "Content-Type: application/json" \
    --data "{\"model\":\"${AI_MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with OPENSHORTS_OK\"}],\"max_tokens\":32}" \
    "${AI_BASE_URL%/}/chat/completions" \
    | python3 -m json.tool
'
```

Do not enable production traffic until both requests succeed.

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

## Configure the dashboard

Open **Settings** and choose:

```text
Custom Endpoint + API Key
```

Then:

1. Enter the same Base URL.
2. Enter the endpoint API key.
3. Wait for automatic model discovery.
4. Select a Gemini model from the dropdown.
5. Click **Save Endpoint**.

The dashboard prioritizes model IDs containing `gemini`.

## Browser CORS requirement

The dashboard calls the endpoint's `/models` route directly for automatic discovery.

External endpoints must allow the OpenShorts origin and these headers:

```text
Authorization
Accept
```

If CORS is blocked, enter the known model ID manually. The FastAPI backend can still use the endpoint for generation because server-to-server requests are not restricted by browser CORS.

For a router running on the same VPS, expose a protected same-origin models path through Nginx rather than opening the router publicly.

## Network security

- Keep FastAPI on `127.0.0.1:8000`.
- Keep the renderer on `127.0.0.1:3100`.
- Expose only Nginx ports 80 and 443.
- Use HTTPS for external AI endpoints.
- Restrict a private router with security groups or localhost binding.
- Do not expose an endpoint without authentication.
- Add application authentication and rate limiting before allowing untrusted users to submit jobs.

## AWS credentials

Use an EC2 IAM instance profile for S3. Do not add permanent AWS access keys to `/etc/openshorts/openshorts.env`.

## Scope limitation

The custom endpoint is used for text-based tasks such as transcript analysis, viral-moment selection, hooks, titles, and descriptions.

Direct Gemini Files API video uploads are not translated to the OpenAI-compatible API. Those operations still require the direct **Google Gemini API Key** provider.

## Rotate the endpoint API key

1. Create a replacement key at the endpoint provider.
2. Update `/etc/openshorts/openshorts.env`.
3. Update the dashboard setting.
4. Restart the backend.
5. Run model discovery and one clipping smoke test.
6. Revoke the old key.

```bash
sudo systemctl restart openshorts-backend
sudo systemctl --no-pager --full status openshorts-backend
```

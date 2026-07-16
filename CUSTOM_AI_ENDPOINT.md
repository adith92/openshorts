# Custom AI Endpoint for OpenShorts

OpenShorts supports OpenAI-compatible endpoints for transcript-based clip analysis while preserving the regular Google Gemini provider.

Supported gateway examples include:

- 9Router
- OmniRoute
- LiteLLM
- OpenRouter-compatible gateways
- internal services exposing `POST /chat/completions`

## Configure from the UI

1. Open **Settings**.
2. Under **AI Provider**, select **OpenAI Compatible / Custom Endpoint**.
3. Enter a Base URL reachable from the OpenShorts backend host.
4. Enter the model or routing alias.
5. Enter the gateway API key.
6. Save the AI settings.
7. Start a Clip Generator job.

Examples:

```text
http://127.0.0.1:20128/v1
https://router.example.com/v1
```

OpenShorts appends `/chat/completions` unless the Base URL already ends with that path.

## Native host networking

The endpoint is called by the FastAPI backend process, not by the browser.

When the gateway runs on the same AWS instance, bind it to localhost and use:

```text
http://127.0.0.1:20128/v1
```

When the gateway runs on another private host, use its private DNS name or private IP and restrict access with security groups.

When the gateway is external, require HTTPS and a valid certificate.

Do not expose an unauthenticated gateway directly to the public internet.

## Environment configuration

The UI is the preferred configuration path. The compatibility layer can also read server variables:

```env
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://127.0.0.1:20128/v1
AI_API_KEY=replace_me
AI_MODEL=auto
AI_TEMPERATURE=0.2
AI_TIMEOUT_SECONDS=180
AI_MAX_TOKENS=4096
```

Store server-side secrets in a protected environment file such as:

```text
/etc/openshorts/openshorts.env
```

Recommended permissions:

```bash
sudo chown root:openshorts /etc/openshorts/openshorts.env
sudo chmod 640 /etc/openshorts/openshorts.env
```

Never commit the real key.

## Supported scope

The custom endpoint supports text-based generation, including transcript-based viral moment selection.

The following Gemini-specific operations are not translated to the OpenAI-compatible API:

- Gemini Files API uploads
- direct video upload to Gemini
- Gemini-specific grounding or tools

Use the regular Gemini provider for those operations.

## Request flow

```text
Settings
  -> encoded per-request AI configuration
  -> X-Gemini-Key compatibility request path
  -> FastAPI subprocess environment
  -> sitecustomize.py
  -> OpenAI-compatible /chat/completions
```

Regular Gemini API keys continue to use the original Google client.

## Test connectivity on the AWS host

Run the test as the same Linux user as the backend service:

```bash
sudo -u openshorts -H bash -lc '
  cd /opt/openshorts
  . .venv/bin/activate
  python - <<"PY"
import httpx
url = "http://127.0.0.1:20128/v1/models"
response = httpx.get(url, timeout=10)
print(response.status_code)
PY
'
```

## Tests

```bash
python -m unittest tests/test_custom_ai_client.py -v
```

## Troubleshooting

### Connection refused

Verify that the gateway is running, listening on the expected interface, and reachable from the backend service user.

```bash
sudo ss -lntp | grep 20128 || true
```

### 401 or 403

The gateway rejected the API key or access policy. Verify the configured key and gateway permissions without printing the secret.

### 404

Use the gateway's OpenAI-compatible base path, usually ending in `/v1`.

### Unsupported `response_format`

The client retries once without `response_format` when a gateway returns HTTP 400 for that option.

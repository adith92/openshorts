# Custom AI Endpoint for OpenShorts

OpenShorts supports OpenAI-compatible endpoints for transcript-based clip analysis while preserving the regular Google Gemini API-key provider as a direct fallback.

Supported gateway examples include:

- LiteLLM
- OpenRouter-compatible gateways
- OmniRoute or similar routers
- internal services exposing `GET /models` and `POST /chat/completions`

## Required endpoint contract

Given a Base URL such as:

```text
https://router.example.com/v1
```

OpenShorts uses:

```text
GET  https://router.example.com/v1/models
POST https://router.example.com/v1/chat/completions
```

The same API key is sent as:

```http
Authorization: Bearer ENDPOINT_API_KEY
```

The model ID selected from the `/models` response is sent unchanged in the `model` field of the chat completion request.

## Configure from the UI

1. Open **Settings**.
2. Select **Custom Endpoint + API Key**.
3. Enter the Base URL.
4. Enter the endpoint API key.
5. Wait for automatic model discovery, or click **Refresh Models**.
6. Choose one of the discovered Gemini models.
7. Save the endpoint.
8. Start a Clip Generator job.

Model discovery begins automatically about 700 milliseconds after both the Base URL and API key are present.

The model selector prioritizes IDs containing `gemini`. When the endpoint returns Gemini and non-Gemini models, the UI shows Gemini models by default and provides an option to display the complete list.

Examples of supported model payloads:

```json
{
  "data": [
    {"id": "google/gemini-2.5-flash"},
    {"id": "google/gemini-2.5-pro"}
  ]
}
```

```json
{
  "models": [
    {"name": "models/gemini-2.5-flash"}
  ]
}
```

OpenShorts also accepts arrays of model strings and common nested `result.data` or `result.models` responses.

## CORS requirement for automatic discovery

The dashboard fetches the models list directly from the configured endpoint so the list can update immediately while the user edits Settings.

External endpoints must allow browser requests from the OpenShorts origin and permit these headers:

```text
Authorization
Accept
```

When the endpoint blocks CORS, automatic discovery shows an error and the UI keeps a manual model-ID fallback. Generation can still work through the FastAPI backend after a valid model ID is entered manually.

For a private router on the same VPS, the cleanest production setup is to expose a protected same-origin path through Nginx rather than opening the router directly to the internet.

## Base URL normalization

OpenShorts accepts any of these forms:

```text
https://router.example.com/v1
https://router.example.com/v1/models
https://router.example.com/v1/chat/completions
```

They normalize to the same API root and produce the corresponding `/models` and `/chat/completions` URLs.

The Base URL must:

- use HTTP or HTTPS;
- not contain embedded username/password credentials;
- not contain a query string or fragment.

Use HTTPS for external routers.

## Server environment fallback

The UI is the preferred configuration path. The Python compatibility layer can also read protected server variables:

```env
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://router.example.com/v1
AI_API_KEY=replace_me
AI_MODEL=google/gemini-2.5-flash
AI_TEMPERATURE=0.2
AI_TIMEOUT_SECONDS=180
AI_MAX_TOKENS=4096
```

Store server-side secrets in:

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

The custom endpoint supports text-based generation, including:

- transcript viral-moment selection;
- timestamps;
- hooks;
- titles;
- descriptions.

The following Gemini-specific operations are not translated to the OpenAI-compatible API:

- Gemini Files API uploads;
- direct video upload to Gemini;
- Gemini-specific grounding or tools.

Use the direct Gemini API-key provider for those operations.

## Request flow

```text
Settings
  -> GET endpoint /models with endpoint API key
  -> user selects a Gemini model ID
  -> encoded per-request AI configuration
  -> X-Gemini-Key compatibility request path
  -> FastAPI subprocess environment
  -> sitecustomize.py
  -> OpenAI-compatible /chat/completions
```

The `X-Gemini-Key` header name remains for backward compatibility. For custom endpoints, its value is an encoded AI configuration rather than a raw Gemini key.

## Test connectivity on the AWS host

Run the test as the same Linux user as the backend service without printing the key:

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

## Tests

```bash
python -m unittest \
  tests/test_custom_ai_client.py \
  tests/test_native_aws_deployment.py \
  -v
```

## Troubleshooting

### Browser reports a CORS error

Allow the OpenShorts web origin on the custom endpoint, or enter a known model ID manually. Do not use a browser extension that disables web security in production.

### Connection refused

Verify that the gateway is running and reachable from both the user's browser for model discovery and the backend host for generation.

### 401 or 403

The endpoint rejected the API key or access policy. Verify the key without printing it to logs.

### 404 on model discovery

Confirm that the Base URL points to the OpenAI-compatible API root. OpenShorts appends `/models` automatically.

### No Gemini models shown

Use **Show all endpoint models** to inspect the complete response. Some routers use aliases that do not contain the word `gemini`.

### Unsupported `response_format`

The generation client retries once without `response_format` when a gateway returns HTTP 400 for that option.

# Custom AI Endpoint for OpenShorts

This branch adds an **OpenAI-compatible custom endpoint** option for automatic viral clip detection.

Supported examples include:

- 9Router
- OmniRoute
- LiteLLM
- OpenRouter-compatible gateways
- Internal gateways exposing `POST /chat/completions`

Google Gemini remains the default and continues to work without configuration changes.

## Configure from the UI

1. Open **Settings**.
2. Under **AI Provider**, choose **OpenAI Compatible / Custom Endpoint**.
3. Enter a Base URL, for example:

   ```text
   http://omniroute:20128/v1
   ```

4. Enter the model or routing alias, for example:

   ```text
   auto
   clip-analysis
   gemini-2.5-flash
   ```

5. Enter the router API key.
6. Click **Save AI**.
7. Start a Clip Generator job normally.

OpenShorts appends `/chat/completions` unless the Base URL already ends with that path.

## Docker networking

The endpoint is called by the **OpenShorts backend container**, not by the browser.

### Router in the same Docker network

Use the service name:

```text
http://omniroute:20128/v1
```

or:

```text
http://9router:20128/v1
```

### Router running on the Docker host

On Docker Desktop:

```text
http://host.docker.internal:20128/v1
```

On Linux, add this to the backend service if the hostname is unavailable:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Do not use `localhost` unless the router runs inside the same backend container.

## Environment configuration

The UI is the easiest option. The compatibility layer can also read server variables:

```env
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://omniroute:20128/v1
AI_API_KEY=replace_me
AI_MODEL=auto
AI_TEMPERATURE=0.2
AI_TIMEOUT_SECONDS=180
AI_MAX_TOKENS=4096
```

When environment mode is used, the existing key field still needs a value because the current OpenShorts API validates that request header before creating a job. Using the Settings UI avoids that limitation.

## Scope

The custom route currently supports **text-based generation**, including the transcript-based viral moment selection used by Clip Generator.

The following Gemini-specific operations are not translated to the OpenAI-compatible API:

- Gemini Files API uploads
- Direct video upload to Gemini
- Gemini-specific grounding or tools

Those operations return a clear error and should be used with the Gemini provider.

## How it works

OpenShorts currently constructs `google.genai.Client` directly. A small runtime compatibility hook intercepts that construction only when a custom configuration is selected:

```text
Settings
  -> encoded per-request AI configuration
  -> existing X-Gemini-Key request path
  -> backend subprocess environment
  -> sitecustomize.py
  -> OpenAI-compatible /chat/completions
```

Normal Gemini keys are passed to the original Google client unchanged.

## Run tests

From the repository root:

```bash
python -m unittest tests/test_custom_ai_client.py -v
```

## Troubleshooting

### Connection refused

Confirm the Base URL is reachable from inside the backend container:

```bash
docker compose exec backend python - <<'PY'
import httpx
print(httpx.get("http://omniroute:20128/v1/models", timeout=10).status_code)
PY
```

### 401 or 403

The router rejected the API key. Check the router key and any required access profile.

### 404

Use the router's OpenAI-compatible base path. Usually it ends with `/v1`.

### Unsupported `response_format`

The client automatically retries once without `response_format` when the router returns HTTP 400.

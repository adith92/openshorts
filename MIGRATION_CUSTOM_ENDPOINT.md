# Migration to Custom Endpoint Model Discovery

Gemini CLI OAuth support has been removed from OpenShorts.

## Previous configuration

Old browser settings may contain the provider:

```text
gemini_cli_oauth
```

The Settings component automatically migrates that saved value to a blank **Custom Endpoint + API Key** form. It does not attempt to reuse OAuth credentials or server paths.

## New configuration

Enter:

```text
Base URL
Endpoint API Key
```

OpenShorts requests:

```text
GET BASE_URL/models
```

and prioritizes returned model IDs containing `gemini`.

After a model is selected, generation uses:

```text
POST BASE_URL/chat/completions
```

with the exact selected model ID.

## Browser storage

The custom endpoint configuration continues to use the existing browser settings compatibility format. The endpoint API key is therefore available to the browser that saves it.

Use OpenShorts only from trusted administrator browsers. For a multi-user public deployment, move endpoint credentials behind an authenticated server-side settings service before allowing untrusted users access.

## CORS

Automatic model discovery is a browser request. External endpoints must allow the OpenShorts origin and the `Authorization` and `Accept` headers.

When discovery is blocked, enter a known model ID using the manual fallback. Server-side generation can still work because browser CORS does not apply to the FastAPI request to the endpoint.

## Removed files

The migration removes:

```text
gemini_cli_oauth_client.py
GEMINI_CLI_OAUTH.md
tests/test_gemini_cli_oauth_client.py
deploy/aws-native/gemini-oauth-login.sh
deploy/aws-native/gemini-oauth-check.sh
```

Remove any obsolete Gemini CLI variables from `/etc/openshorts/openshorts.env` and replace them with:

```dotenv
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://router.example.com/v1
AI_API_KEY=replace_with_endpoint_api_key
AI_MODEL=google/gemini-2.5-flash
AI_TEMPERATURE=0.2
AI_TIMEOUT_SECONDS=180
AI_MAX_TOKENS=4096
```

# Custom endpoint quick checklist

- [ ] Base URL points to the OpenAI-compatible API root.
- [ ] `GET /models` succeeds with the endpoint API key.
- [ ] The desired Gemini model ID appears in the response.
- [ ] `POST /chat/completions` succeeds with that exact model ID.
- [ ] The dashboard origin is allowed by the endpoint CORS policy.
- [ ] The endpoint uses HTTPS when it is not on localhost or a private network.
- [ ] `/etc/openshorts/openshorts.env` is owned by `root:openshorts` with mode `0640`.
- [ ] API keys are absent from Git, screenshots, logs, and shell history.
- [ ] `sudo bash deploy/aws-native/custom-endpoint-check.sh` passes on the VPS.

"""Runtime hook that adds alternate AI providers without breaking Gemini."""

try:
    from google import genai as _genai

    from custom_ai_client import OpenAICompatibleClient, resolve_custom_ai_config
    from gemini_cli_oauth_client import (
        GeminiCliOAuthClient,
        resolve_gemini_cli_oauth_config,
    )

    _original_client = _genai.Client

    def _openshorts_client_factory(*args, **kwargs):
        api_key = kwargs.get("api_key")
        if api_key is None and args:
            api_key = args[0]

        cli_config = resolve_gemini_cli_oauth_config(api_key)
        if cli_config is not None:
            print(
                "[CustomAI] Gemini CLI OAuth provider enabled "
                f"(model={cli_config.model})"
            )
            return GeminiCliOAuthClient(cli_config)

        custom_config = resolve_custom_ai_config(api_key)
        if custom_config is not None:
            print(
                "[CustomAI] OpenAI-compatible provider enabled "
                f"(endpoint={custom_config.safe_endpoint_label}, "
                f"model={custom_config.model})"
            )
            return OpenAICompatibleClient(custom_config)

        return _original_client(*args, **kwargs)

    _genai.Client = _openshorts_client_factory
except Exception as exc:
    # Never block OpenShorts startup if optional compatibility providers fail.
    print(f"[CustomAI] Compatibility hook was not installed: {exc}")

"""Runtime hook that adds OpenAI-compatible endpoint support without breaking Gemini."""

try:
    from google import genai as _genai

    from custom_ai_client import OpenAICompatibleClient, resolve_custom_ai_config

    _original_client = _genai.Client

    def _openshorts_client_factory(*args, **kwargs):
        api_key = kwargs.get("api_key")
        if api_key is None and args:
            api_key = args[0]

        custom_config = resolve_custom_ai_config(api_key)
        if custom_config is not None:
            print(
                "[CustomAI] OpenAI-compatible provider enabled "
                f"(endpoint={custom_config.base_url}, model={custom_config.model})"
            )
            return OpenAICompatibleClient(custom_config)

        return _original_client(*args, **kwargs)

    _genai.Client = _openshorts_client_factory
except Exception as exc:
    # Never block OpenShorts startup if this optional compatibility hook cannot initialize.
    print(f"[CustomAI] Compatibility hook was not installed: {exc}")

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlparse

import httpx

CONFIG_PREFIX = "OPENSHORTS_AI_V1:"
_CUSTOM_PROVIDERS = {"openai_compatible", "custom", "openai-compatible"}


class CustomAIError(RuntimeError):
    """Raised when a custom OpenAI-compatible provider cannot complete a request."""


@dataclass(frozen=True)
class CustomAIConfig:
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.2
    timeout_seconds: float = 180.0
    max_tokens: int = 4096

    @property
    def chat_completions_url(self) -> str:
        base = self.base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    @property
    def safe_endpoint_label(self) -> str:
        parsed = urlparse(self.base_url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _decode_embedded_config(value: str) -> dict[str, Any] | None:
    if not value or not value.startswith(CONFIG_PREFIX):
        return None

    encoded = value[len(CONFIG_PREFIX):]
    try:
        payload = base64.b64decode(encoded, validate=True).decode("utf-8")
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CustomAIError("The saved custom AI configuration is invalid. Save it again in Settings.") from exc

    if not isinstance(data, dict):
        raise CustomAIError("The saved custom AI configuration must be a JSON object.")
    return data


def _validate_base_url(value: str) -> str:
    base_url = (value or "").strip().rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CustomAIError("Custom AI Base URL must be a valid http:// or https:// URL.")
    if parsed.username or parsed.password:
        raise CustomAIError("Put credentials in the API key field, not in the Base URL.")
    if parsed.query or parsed.fragment:
        raise CustomAIError("Custom AI Base URL must not contain a query string or fragment.")
    if "\n" in base_url or "\r" in base_url:
        raise CustomAIError("Custom AI Base URL contains invalid characters.")
    return base_url


def _number(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


def _integer(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


def resolve_custom_ai_config(api_key_argument: str | None) -> CustomAIConfig | None:
    """Resolve custom settings from the encoded browser value or container environment."""
    embedded = _decode_embedded_config(api_key_argument or "")

    if embedded is not None:
        provider = str(embedded.get("provider", "")).strip().lower()
        if provider not in _CUSTOM_PROVIDERS:
            return None
        raw_key = str(embedded.get("apiKey", "")).strip()
        base_url = _validate_base_url(str(embedded.get("baseUrl", "")))
        model = str(embedded.get("model", "")).strip()
        temperature = _number(embedded.get("temperature"), 0.2, 0.0, 2.0)
        timeout_seconds = _number(embedded.get("timeoutSeconds"), 180.0, 10.0, 900.0)
        max_tokens = _integer(embedded.get("maxTokens"), 4096, 256, 32768)
    else:
        provider = os.getenv("AI_PROVIDER", "").strip().lower()
        if provider not in _CUSTOM_PROVIDERS:
            return None
        raw_key = (os.getenv("AI_API_KEY") or api_key_argument or "").strip()
        base_url = _validate_base_url(os.getenv("AI_BASE_URL", ""))
        model = os.getenv("AI_MODEL", "").strip()
        temperature = _number(os.getenv("AI_TEMPERATURE"), 0.2, 0.0, 2.0)
        timeout_seconds = _number(os.getenv("AI_TIMEOUT_SECONDS"), 180.0, 10.0, 900.0)
        max_tokens = _integer(
            os.getenv("AI_MAX_TOKENS") or os.getenv("AI_MAX_OUTPUT_TOKENS"),
            4096,
            256,
            32768,
        )

    if not raw_key:
        raise CustomAIError("Custom AI API key is missing.")
    if "\n" in raw_key or "\r" in raw_key:
        raise CustomAIError("Custom AI API key contains invalid characters.")
    if not model:
        raise CustomAIError("Custom AI model is missing.")

    return CustomAIConfig(
        base_url=base_url,
        api_key=raw_key,
        model=model,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
        max_tokens=max_tokens,
    )


def _contents_to_text(contents: Any) -> str:
    if isinstance(contents, str):
        return contents
    if isinstance(contents, (list, tuple)):
        parts: list[str] = []
        for item in contents:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif hasattr(item, "text") and isinstance(item.text, str):
                parts.append(item.text)
            else:
                raise CustomAIError(
                    "This custom endpoint currently supports text-only AI requests. "
                    "Gemini file/video inputs still require the Gemini provider."
                )
        return "\n".join(parts)
    if isinstance(contents, dict) and isinstance(contents.get("text"), str):
        return contents["text"]
    raise CustomAIError("Unsupported custom AI request content.")


def _extract_content(message_content: Any) -> str:
    if isinstance(message_content, str):
        return message_content
    if isinstance(message_content, list):
        text_parts: list[str] = []
        for part in message_content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text_parts.append(part["text"])
        if text_parts:
            return "\n".join(text_parts)
    raise CustomAIError("Custom AI endpoint returned an unsupported message format.")


class _UnsupportedFilesAPI:
    def upload(self, *args: Any, **kwargs: Any) -> Any:
        raise CustomAIError(
            "Gemini Files API is unavailable with a custom OpenAI-compatible endpoint. "
            "Use Gemini for features that upload video files directly to the model."
        )


class _CustomModelsAPI:
    def __init__(self, client: "OpenAICompatibleClient") -> None:
        self._client = client

    def generate_content(self, model: str | None = None, contents: Any = None, **kwargs: Any) -> Any:
        return self._client.generate_content(model=model, contents=contents, **kwargs)


class OpenAICompatibleClient:
    """Small compatibility shim for the subset of google-genai used by OpenShorts."""

    def __init__(self, config: CustomAIConfig, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config
        self.models = _CustomModelsAPI(self)
        self.files = _UnsupportedFilesAPI()
        self._transport = transport

    def generate_content(self, model: str | None = None, contents: Any = None, **kwargs: Any) -> Any:
        prompt = _contents_to_text(contents)
        selected_model = self.config.model or model
        payload: dict[str, Any] = {
            "model": selected_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Follow the requested output format exactly. Return valid JSON when JSON is requested.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        prompt_lower = prompt.lower()
        if "return only valid json" in prompt_lower or ("output" in prompt_lower and "json" in prompt_lower):
            payload["response_format"] = {"type": "json_object"}

        timeout = httpx.Timeout(
            connect=min(15.0, self.config.timeout_seconds),
            read=self.config.timeout_seconds,
            write=min(30.0, self.config.timeout_seconds),
            pool=min(15.0, self.config.timeout_seconds),
        )
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=timeout, transport=self._transport) as client:
                response = client.post(self.config.chat_completions_url, headers=headers, json=payload)

                # Routers vary in which OpenAI parameters they accept. Retry only for
                # payload compatibility errors, never for authentication/rate limits.
                if response.status_code == 400 and "response_format" in payload:
                    payload.pop("response_format", None)
                    response = client.post(self.config.chat_completions_url, headers=headers, json=payload)

                if response.status_code == 400 and "max_tokens" in payload:
                    error_text = response.text.lower()
                    if "max_tokens" in error_text or "unsupported" in error_text:
                        payload["max_completion_tokens"] = payload.pop("max_tokens")
                        response = client.post(self.config.chat_completions_url, headers=headers, json=payload)

                if response.status_code == 400 and "temperature" in payload:
                    error_text = response.text.lower()
                    if "temperature" in error_text or "unsupported" in error_text:
                        payload.pop("temperature", None)
                        response = client.post(self.config.chat_completions_url, headers=headers, json=payload)

                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise CustomAIError("Custom AI endpoint timed out.") from exc
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500].replace(self.config.api_key, "***")
            raise CustomAIError(
                f"Custom AI endpoint returned HTTP {exc.response.status_code}: {body}"
            ) from exc
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise CustomAIError(f"Custom AI endpoint request failed: {exc}") from exc

        try:
            choice = data["choices"][0]
            text = _extract_content(choice["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise CustomAIError("Custom AI endpoint response is missing choices[0].message.content.") from exc

        usage = data.get("usage") or {}
        custom_usage_metadata = None
        if isinstance(usage, dict) and usage:
            custom_usage_metadata = SimpleNamespace(
                prompt_token_count=int(usage.get("prompt_tokens") or 0),
                candidates_token_count=int(usage.get("completion_tokens") or 0),
                total_token_count=int(usage.get("total_tokens") or 0),
            )

        return SimpleNamespace(
            text=text,
            # main.py currently applies hard-coded Gemini pricing whenever this field
            # is present. Keep it None so custom-router usage is not mislabeled/costed.
            usage_metadata=None,
            custom_usage_metadata=custom_usage_metadata,
            model_version=data.get("model", selected_model),
        )

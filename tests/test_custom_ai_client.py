import base64
import json
import os
import unittest
from unittest.mock import patch

import httpx

from custom_ai_client import (
    CONFIG_PREFIX,
    CustomAIError,
    OpenAICompatibleClient,
    resolve_custom_ai_config,
)


def encoded_config(**overrides):
    payload = {
        "provider": "openai_compatible",
        "baseUrl": "http://omniroute:20128/v1",
        "apiKey": "test-secret",
        "model": "auto",
        "temperature": 0.2,
        "timeoutSeconds": 30,
        "maxTokens": 4096,
    }
    payload.update(overrides)
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    return CONFIG_PREFIX + encoded


class CustomAIConfigTests(unittest.TestCase):
    def test_decodes_browser_configuration(self):
        config = resolve_custom_ai_config(encoded_config())
        self.assertEqual(config.model, "auto")
        self.assertEqual(
            config.chat_completions_url,
            "http://omniroute:20128/v1/chat/completions",
        )

    def test_accepts_full_chat_completions_url(self):
        config = resolve_custom_ai_config(
            encoded_config(baseUrl="https://router.example/v1/chat/completions")
        )
        self.assertEqual(
            config.chat_completions_url,
            "https://router.example/v1/chat/completions",
        )

    def test_plain_gemini_key_keeps_original_provider(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(resolve_custom_ai_config("AIza-test"))

    def test_rejects_invalid_scheme(self):
        with self.assertRaises(CustomAIError):
            resolve_custom_ai_config(encoded_config(baseUrl="file:///etc/passwd"))


class OpenAICompatibleClientTests(unittest.TestCase):
    def test_returns_google_genai_compatible_response(self):
        config = resolve_custom_ai_config(encoded_config())

        def handler(request):
            self.assertEqual(request.headers["authorization"], "Bearer test-secret")
            body = json.loads(request.content.decode("utf-8"))
            self.assertEqual(body["model"], "auto")
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "{\"shorts\": []}"}}],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 2,
                        "total_tokens": 12,
                    },
                    "model": "routed-model",
                },
            )

        client = OpenAICompatibleClient(config, transport=httpx.MockTransport(handler))
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="RETURN ONLY VALID JSON",
        )

        self.assertEqual(response.text, '{"shorts": []}')
        self.assertEqual(response.usage_metadata.prompt_token_count, 10)
        self.assertEqual(response.usage_metadata.candidates_token_count, 2)

    def test_retries_without_response_format_on_400(self):
        config = resolve_custom_ai_config(encoded_config())
        calls = []

        def handler(request):
            body = json.loads(request.content.decode("utf-8"))
            calls.append(body)
            if len(calls) == 1:
                return httpx.Response(400, json={"error": "unsupported response_format"})
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "{\"shorts\": []}"}}]},
            )

        client = OpenAICompatibleClient(config, transport=httpx.MockTransport(handler))
        response = client.models.generate_content(contents="RETURN ONLY VALID JSON")

        self.assertEqual(response.text, '{"shorts": []}')
        self.assertIn("response_format", calls[0])
        self.assertNotIn("response_format", calls[1])


if __name__ == "__main__":
    unittest.main()

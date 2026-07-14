import base64
import json
import subprocess
import unittest
from unittest.mock import patch

from gemini_cli_oauth_client import (
    CONFIG_PREFIX,
    GeminiCliOAuthClient,
    GeminiCliOAuthConfig,
    GeminiCliOAuthError,
    resolve_gemini_cli_oauth_config,
)


def encoded_config(**overrides):
    payload = {
        "provider": "gemini_cli_oauth",
        "model": "auto",
        "timeoutSeconds": 30,
    }
    payload.update(overrides)
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    return CONFIG_PREFIX + encoded


class GeminiCliOAuthConfigTests(unittest.TestCase):
    def test_resolves_without_api_key(self):
        config = resolve_gemini_cli_oauth_config(encoded_config())
        self.assertIsInstance(config, GeminiCliOAuthConfig)
        self.assertEqual(config.model, "auto")
        self.assertEqual(config.safe_endpoint_label, "gemini-cli-oauth")

    def test_ignores_other_provider(self):
        self.assertIsNone(
            resolve_gemini_cli_oauth_config(
                encoded_config(provider="openai_compatible")
            )
        )


class GeminiCliOAuthClientTests(unittest.TestCase):
    def setUp(self):
        self.config = GeminiCliOAuthConfig(
            model="auto",
            timeout_seconds=30,
            binary="gemini",
            working_directory="/tmp/openshorts-gemini-cli-test",
        )

    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_reads_official_cli_json_output(self, run_mock, _which_mock):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "session_id": "session-1",
                    "response": '{"shorts": []}',
                    "stats": {"models": {}},
                }
            ),
            stderr="",
        )

        client = GeminiCliOAuthClient(self.config)
        response = client.models.generate_content(
            contents="RETURN ONLY VALID JSON"
        )

        self.assertEqual(response.text, '{"shorts": []}')
        command = run_mock.call_args.args[0]
        self.assertIn("--output-format", command)
        self.assertIn("json", command)
        self.assertIn("--approval-mode", command)
        self.assertIn("plan", command)
        self.assertNotIn("--model", command)

    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_returns_clear_login_instruction(self, run_mock, _which_mock):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Authentication required. Sign in with Google.",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaisesRegex(
            GeminiCliOAuthError,
            "docker compose exec backend",
        ):
            client.models.generate_content(contents="hello")


if __name__ == "__main__":
    unittest.main()

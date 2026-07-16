import base64
import json
import os
import subprocess
import unittest
from unittest.mock import patch

from gemini_cli_oauth_client import (
    CONFIG_PREFIX,
    GeminiCliOAuthClient,
    GeminiCliOAuthConfig,
    GeminiCliOAuthError,
    get_gemini_cli_oauth_status,
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
    @patch.dict(
        os.environ,
        {
            "OPENSHORTS_SERVER_GEMINI_OAUTH": "true",
            "GEMINI_CLI_BINARY": "/usr/local/bin/gemini",
            "GEMINI_CLI_WORKING_DIR": "/var/lib/openshorts/tmp/gemini-cli",
        },
        clear=False,
    )
    def test_resolves_without_api_key(self):
        config = resolve_gemini_cli_oauth_config(encoded_config())
        self.assertIsInstance(config, GeminiCliOAuthConfig)
        self.assertEqual(config.model, "auto")
        self.assertEqual(config.safe_endpoint_label, "gemini-cli-oauth")
        self.assertEqual(config.binary, "/usr/local/bin/gemini")
        self.assertEqual(
            config.working_directory,
            "/var/lib/openshorts/tmp/gemini-cli",
        )

    @patch.dict(
        os.environ,
        {
            "OPENSHORTS_SERVER_GEMINI_OAUTH": "true",
            "GEMINI_CLI_BINARY": "/usr/local/bin/gemini",
            "GEMINI_CLI_WORKING_DIR": "/safe/server/path",
        },
        clear=False,
    )
    def test_client_cannot_override_server_binary_or_working_directory(self):
        config = resolve_gemini_cli_oauth_config(
            encoded_config(
                binary="/tmp/untrusted-binary",
                workingDirectory="/tmp/untrusted-directory",
            )
        )
        self.assertEqual(config.binary, "/usr/local/bin/gemini")
        self.assertEqual(config.working_directory, "/safe/server/path")

    @patch.dict(
        os.environ,
        {"OPENSHORTS_SERVER_GEMINI_OAUTH": "false"},
        clear=False,
    )
    def test_server_oauth_must_be_explicitly_enabled(self):
        with self.assertRaisesRegex(
            GeminiCliOAuthError,
            "OPENSHORTS_SERVER_GEMINI_OAUTH=true",
        ):
            resolve_gemini_cli_oauth_config(encoded_config())

    @patch.dict(
        os.environ,
        {"OPENSHORTS_SERVER_GEMINI_OAUTH": "true"},
        clear=False,
    )
    def test_ignores_other_provider(self):
        self.assertIsNone(
            resolve_gemini_cli_oauth_config(
                encoded_config(provider="openai_compatible")
            )
        )

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch.dict(
        os.environ,
        {"OPENSHORTS_SERVER_GEMINI_OAUTH": "true"},
        clear=False,
    )
    def test_status_reports_ready_without_exposing_credentials(
        self,
        _which_mock,
        _credential_mock,
    ):
        status = get_gemini_cli_oauth_status()
        self.assertTrue(status["enabled"])
        self.assertTrue(status["binaryInstalled"])
        self.assertTrue(status["credentialsPresent"])
        self.assertTrue(status["ready"])
        self.assertNotIn("token", json.dumps(status).lower())
        self.assertNotIn("credentialDirectory", status)


class GeminiCliOAuthClientTests(unittest.TestCase):
    def setUp(self):
        self.config = GeminiCliOAuthConfig(
            model="auto",
            timeout_seconds=30,
            binary="gemini",
            working_directory="/tmp/openshorts-gemini-cli-test",
        )

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_reads_official_cli_json_output(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
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
        self.assertEqual(command[command.index("-p") + 1], "")
        self.assertEqual(
            run_mock.call_args.kwargs["input"],
            "RETURN ONLY VALID JSON",
        )

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=False)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    def test_returns_native_login_instruction_when_credentials_are_missing(
        self,
        _which_mock,
        _credential_mock,
    ):
        client = GeminiCliOAuthClient(self.config)
        with self.assertRaisesRegex(
            GeminiCliOAuthError,
            "sudo -u openshorts",
        ):
            client.models.generate_content(contents="hello")

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_returns_clear_relogin_instruction_when_session_is_expired(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Authentication required. Sign in with Google.",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaisesRegex(
            GeminiCliOAuthError,
            "session on the VPS is missing or expired",
        ):
            client.models.generate_content(contents="hello")

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_does_not_expose_cli_error_output(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="upstream failure bearer super-secret-value",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaises(GeminiCliOAuthError) as raised:
            client.models.generate_content(contents="hello")

        self.assertNotIn("super-secret-value", str(raised.exception))

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_does_not_expose_json_error_payload(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"error": {"message": "bearer super-secret-json-value"}}
            ),
            stderr="",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaises(GeminiCliOAuthError) as raised:
            client.models.generate_content(contents="hello")

        self.assertNotIn("super-secret-json-value", str(raised.exception))

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_timeout_does_not_retain_cli_output(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.side_effect = subprocess.TimeoutExpired(
            cmd=["gemini"],
            timeout=30,
            output="super-secret-timeout-output",
            stderr="super-secret-timeout-error",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaises(GeminiCliOAuthError) as raised:
            client.models.generate_content(contents="hello")

        self.assertIsNone(raised.exception.__cause__)
        self.assertIsNone(raised.exception.__context__)
        self.assertNotIn("super-secret", str(raised.exception))

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_auth_error_in_stdout_is_actionable_when_stderr_has_warning(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="Authentication required. Sign in with Google.",
            stderr="Node emitted a warning.",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaisesRegex(
            GeminiCliOAuthError,
            "session on the VPS is missing or expired",
        ):
            client.models.generate_content(contents="hello")

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_malformed_json_does_not_retain_cli_output(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="not-json super-secret-invalid-output",
            stderr="",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaises(GeminiCliOAuthError) as raised:
            client.models.generate_content(contents="hello")

        self.assertIsNone(raised.exception.__context__)
        self.assertNotIn("super-secret-invalid-output", str(raised.exception))

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_oauth_words_do_not_misclassify_non_auth_failure(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="OAuth credentials loaded; requested model is unavailable.",
            stderr="",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaises(GeminiCliOAuthError) as raised:
            client.models.generate_content(contents="hello")

        self.assertNotIn("missing or expired", str(raised.exception))

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_assign_input_error_is_not_misclassified_as_sign_in_failure(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="Failed to assign input buffer.",
            stderr="",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaises(GeminiCliOAuthError) as raised:
            client.models.generate_content(contents="hello")

        self.assertNotIn("missing or expired", str(raised.exception))

    @patch("gemini_cli_oauth_client._credential_files_exist", return_value=True)
    @patch("gemini_cli_oauth_client.shutil.which", return_value="/usr/local/bin/gemini")
    @patch("gemini_cli_oauth_client.subprocess.run")
    def test_json_auth_error_returns_safe_relogin_instruction(
        self,
        run_mock,
        _which_mock,
        _credential_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"error": {"message": "Authentication required secret-value"}}
            ),
            stderr="",
        )

        client = GeminiCliOAuthClient(self.config)
        with self.assertRaisesRegex(
            GeminiCliOAuthError,
            "session on the VPS is missing or expired",
        ) as raised:
            client.models.generate_content(contents="hello")

        self.assertNotIn("secret-value", str(raised.exception))


if __name__ == "__main__":
    unittest.main()

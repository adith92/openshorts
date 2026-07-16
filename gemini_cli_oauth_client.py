from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

CONFIG_PREFIX = "OPENSHORTS_AI_V1:"
_GEMINI_CLI_PROVIDERS = {
    "gemini_cli_oauth",
    "gemini-cli-oauth",
    "gemini_cli",
    "gemini-cli",
}
_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}


class GeminiCliOAuthError(RuntimeError):
    """Raised when Gemini CLI OAuth cannot complete a request."""


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES


def server_oauth_enabled() -> bool:
    """Return whether the VPS administrator explicitly enabled server OAuth."""
    return _env_bool("OPENSHORTS_SERVER_GEMINI_OAUTH", False)


def _server_home() -> str:
    return (os.getenv("HOME") or "/var/lib/openshorts").strip() or "/var/lib/openshorts"


def _server_binary() -> str:
    return (os.getenv("GEMINI_CLI_BINARY") or "gemini").strip() or "gemini"


def _server_working_directory() -> str:
    return (
        os.getenv("GEMINI_CLI_WORKING_DIR")
        or "/var/lib/openshorts/tmp/gemini-cli"
    ).strip() or "/var/lib/openshorts/tmp/gemini-cli"


def _server_credential_directory() -> Path:
    configured = (os.getenv("GEMINI_CLI_CREDENTIAL_DIR") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path(_server_home()).expanduser() / ".gemini"


def _credential_files_exist(directory: Path) -> bool:
    try:
        return directory.is_dir() and any(path.is_file() for path in directory.rglob("*"))
    except OSError:
        return False


def get_gemini_cli_oauth_status() -> dict[str, Any]:
    """Return non-sensitive server OAuth readiness information."""
    binary_setting = _server_binary()
    binary_path = shutil.which(binary_setting)
    credential_directory = _server_credential_directory()
    credentials_present = _credential_files_exist(credential_directory)
    enabled = server_oauth_enabled()

    return {
        "enabled": enabled,
        "provider": "gemini_cli_oauth",
        "scope": "text_only",
        "binaryInstalled": bool(binary_path),
        "credentialsPresent": credentials_present,
        "ready": enabled and bool(binary_path) and credentials_present,
        "model": (os.getenv("OPENSHORTS_GEMINI_MODEL") or "auto").strip() or "auto",
        "timeoutSeconds": _number(
            os.getenv("OPENSHORTS_GEMINI_TIMEOUT_SECONDS"),
            180.0,
            10.0,
            900.0,
        ),
    }


@dataclass(frozen=True)
class GeminiCliOAuthConfig:
    model: str = "auto"
    timeout_seconds: float = 180.0
    binary: str = "gemini"
    working_directory: str = "/var/lib/openshorts/tmp/gemini-cli"

    @property
    def safe_endpoint_label(self) -> str:
        return "gemini-cli-oauth"


def _number(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


def _decode_embedded_config(value: str) -> dict[str, Any] | None:
    if not value or not value.startswith(CONFIG_PREFIX):
        return None

    encoded = value[len(CONFIG_PREFIX):]
    try:
        payload = base64.b64decode(encoded, validate=True).decode("utf-8")
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GeminiCliOAuthError(
            "The saved Gemini CLI OAuth configuration is invalid. "
            "Save it again in Settings."
        ) from exc

    if not isinstance(data, dict):
        raise GeminiCliOAuthError(
            "The saved Gemini CLI OAuth configuration must be a JSON object."
        )
    return data


def _build_config(model: Any = None, timeout_seconds: Any = None) -> GeminiCliOAuthConfig:
    """Build config using client-safe fields and server-controlled runtime paths."""
    server_model = (os.getenv("OPENSHORTS_GEMINI_MODEL") or "auto").strip() or "auto"
    requested_model = str(model or server_model).strip() or server_model
    server_timeout = _number(
        os.getenv("OPENSHORTS_GEMINI_TIMEOUT_SECONDS"),
        180.0,
        10.0,
        900.0,
    )

    return GeminiCliOAuthConfig(
        model=requested_model,
        timeout_seconds=_number(timeout_seconds, server_timeout, 10.0, 900.0),
        binary=_server_binary(),
        working_directory=_server_working_directory(),
    )


def resolve_gemini_cli_oauth_config(
    api_key_argument: str | None,
) -> GeminiCliOAuthConfig | None:
    """Resolve OAuth settings while keeping credentials and paths server-side."""
    embedded = _decode_embedded_config(api_key_argument or "")

    if embedded is not None:
        provider = str(embedded.get("provider", "")).strip().lower()
        if provider not in _GEMINI_CLI_PROVIDERS:
            return None
        if not server_oauth_enabled():
            raise GeminiCliOAuthError(
                "Server Gemini OAuth is disabled. Set "
                "OPENSHORTS_SERVER_GEMINI_OAUTH=true in the protected VPS "
                "service environment, then restart openshorts-backend."
            )

        # Deliberately ignore client-supplied binary and workingDirectory values.
        # Those are privileged server settings and must never be controlled by a browser.
        return _build_config(
            model=embedded.get("model"),
            timeout_seconds=embedded.get("timeoutSeconds"),
        )

    provider = os.getenv("AI_PROVIDER", "").strip().lower()
    if provider not in _GEMINI_CLI_PROVIDERS:
        return None
    if not server_oauth_enabled():
        raise GeminiCliOAuthError(
            "AI_PROVIDER requests Gemini CLI OAuth, but server OAuth is disabled."
        )

    return _build_config(
        model=os.getenv("AI_MODEL"),
        timeout_seconds=os.getenv("AI_TIMEOUT_SECONDS"),
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
                raise GeminiCliOAuthError(
                    "Gemini CLI OAuth currently supports text-only requests. "
                    "Use the Gemini API provider for direct file/video input."
                )
        return "\n".join(parts)

    if isinstance(contents, dict) and isinstance(contents.get("text"), str):
        return contents["text"]

    raise GeminiCliOAuthError("Unsupported Gemini CLI OAuth request content.")


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise GeminiCliOAuthError(
                "Gemini CLI did not return valid JSON output."
            )
        try:
            value = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise GeminiCliOAuthError(
                "Gemini CLI did not return valid JSON output."
            ) from exc

    if not isinstance(value, dict):
        raise GeminiCliOAuthError(
            "Gemini CLI returned an unexpected JSON payload."
        )
    return value


class _UnsupportedFilesAPI:
    def upload(self, *args: Any, **kwargs: Any) -> Any:
        raise GeminiCliOAuthError(
            "Gemini CLI OAuth does not expose the Gemini Files API. "
            "Use the Gemini API provider for direct video uploads."
        )


class _GeminiCliModelsAPI:
    def __init__(self, client: "GeminiCliOAuthClient") -> None:
        self._client = client

    def generate_content(
        self,
        model: str | None = None,
        contents: Any = None,
        **kwargs: Any,
    ) -> Any:
        return self._client.generate_content(
            model=model,
            contents=contents,
            **kwargs,
        )


class GeminiCliOAuthClient:
    """Use the official Gemini CLI and its persistent VPS OAuth session."""

    def __init__(self, config: GeminiCliOAuthConfig) -> None:
        self.config = config
        self.models = _GeminiCliModelsAPI(self)
        self.files = _UnsupportedFilesAPI()

    def generate_content(
        self,
        model: str | None = None,
        contents: Any = None,
        **kwargs: Any,
    ) -> Any:
        prompt = _contents_to_text(contents)
        selected_model = self.config.model or model or "auto"

        binary = shutil.which(self.config.binary)
        if not binary:
            raise GeminiCliOAuthError(
                "Gemini CLI is not installed on the OpenShorts VPS. "
                "Install @google/gemini-cli and verify GEMINI_CLI_BINARY."
            )

        credential_directory = _server_credential_directory()
        if not _credential_files_exist(credential_directory):
            raise GeminiCliOAuthError(
                "No persistent Gemini OAuth session was found for the "
                "OpenShorts service user. Log in once on the VPS with: "
                "sudo -u openshorts -H env HOME=/var/lib/openshorts "
                "NO_BROWSER=true GOOGLE_GENAI_USE_GCA=true "
                "GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true "
                "GEMINI_CLI_WORKING_DIR=/var/lib/openshorts/tmp/gemini-cli "
                "gemini"
            )

        os.makedirs(self.config.working_directory, exist_ok=True)

        command = [
            binary,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--approval-mode",
            "plan",
            "--skip-trust",
        ]
        if selected_model.lower() not in {"", "auto", "default"}:
            command.extend(["--model", selected_model])

        environment = os.environ.copy()
        environment.setdefault("HOME", _server_home())
        environment.setdefault("GOOGLE_GENAI_USE_GCA", "true")
        environment.setdefault("GEMINI_FORCE_ENCRYPTED_FILE_STORAGE", "true")
        environment.setdefault("NO_BROWSER", "true")

        try:
            result = subprocess.run(
                command,
                cwd=self.config.working_directory,
                env=environment,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise GeminiCliOAuthError(
                "Gemini CLI OAuth request timed out."
            ) from exc
        except OSError as exc:
            raise GeminiCliOAuthError(
                f"Could not start Gemini CLI: {exc}"
            ) from exc

        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or "").strip()[-1200:]
            lowered = error_text.lower()

            if any(
                marker in lowered
                for marker in (
                    "authenticate",
                    "authentication",
                    "sign in",
                    "login",
                    "oauth",
                    "credentials",
                )
            ):
                raise GeminiCliOAuthError(
                    "The Gemini OAuth session on the VPS is missing or expired. "
                    "Run the one-time login again as the openshorts service user."
                )

            raise GeminiCliOAuthError(
                f"Gemini CLI request failed with exit code "
                f"{result.returncode}: {error_text or 'No error output'}"
            )

        payload = _extract_json_object(result.stdout)

        if payload.get("error"):
            error = payload["error"]
            message = (
                str(error.get("message") or error)
                if isinstance(error, dict)
                else str(error)
            )
            raise GeminiCliOAuthError(
                f"Gemini CLI returned an error: {message[:1000]}"
            )

        response_text = payload.get("response")
        if not isinstance(response_text, str) or not response_text.strip():
            raise GeminiCliOAuthError(
                "Gemini CLI JSON output did not include a response."
            )

        return SimpleNamespace(
            text=response_text,
            usage_metadata=None,
            custom_usage_metadata=payload.get("stats"),
            model_version=selected_model,
        )

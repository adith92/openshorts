from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CustomEndpointMigrationTests(unittest.TestCase):
    def test_active_source_has_no_gemini_cli_runtime(self):
        excluded_directories = {".git", "node_modules", "dist", ".deploy"}
        stale_markers = (
            "gemini_cli_oauth_client",
            "OPENSHORTS_SERVER_GEMINI_OAUTH",
            "GEMINI_CLI_BINARY",
            "gemini-oauth-login.sh",
            "gemini-oauth-check.sh",
        )

        matches = []
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if any(part in excluded_directories for part in path.parts):
                continue
            if path.name == "test_custom_endpoint_migration.py":
                continue
            if path.suffix.lower() not in {
                ".py",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".md",
                ".yml",
                ".yaml",
                ".sh",
                ".example",
            }:
                continue

            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in stale_markers:
                if marker in text:
                    matches.append(f"{path.relative_to(ROOT)}: {marker}")

        self.assertEqual([], matches)

    def test_custom_endpoint_ui_contains_model_discovery_controls(self):
        source = (
            ROOT / "dashboard/src/components/AIProviderSettings.jsx"
        ).read_text(encoding="utf-8")

        for required_text in (
            "Custom Endpoint + API Key",
            "Refresh Models",
            "Gemini Model",
            "buildModelsUrl",
            "extractModelIds",
            "Authorization",
        ):
            self.assertIn(required_text, source)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CustomEndpointCheckScriptTests(unittest.TestCase):
    def test_script_uses_models_and_chat_completions(self):
        source = (
            ROOT / "deploy/aws-native/custom-endpoint-check.sh"
        ).read_text(encoding="utf-8")

        for required_text in (
            'MODELS_URL="$API_ROOT/models"',
            'CHAT_URL="$API_ROOT/chat/completions"',
            'Authorization: Bearer ${AI_API_KEY}',
            'AI_MODEL',
            'OPENSHORTS_OK',
        ):
            self.assertIn(required_text, source)

        self.assertNotIn("set -x", source)
        self.assertNotIn("echo $AI_API_KEY", source)
        self.assertNotIn("echo ${AI_API_KEY}", source)


if __name__ == "__main__":
    unittest.main()

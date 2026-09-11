import tempfile
import unittest
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from env_config import env_report, parse_env_file  # noqa: E402


class EnvConfigTests(unittest.TestCase):
    def test_parses_canonical_and_legacy_lines_without_exposing_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / ".env"
            path.write_text(
                "BASEURL=https://images.example.test\n"
                "APIKEY=secret-value\n"
                "IMAGE_MODEL:gpt-image-2.5\n"
                "IMAGE_DEFAULT_RESOLUTION=1024x1024\n",
                encoding="utf-8",
            )
            values = parse_env_file(path)
            report = env_report(Path(temp))

        self.assertEqual(values["IMAGE_MODEL"], "gpt-image-2.5")
        self.assertTrue(report["image"]["configured"])
        self.assertEqual(report["image"]["model"], "gpt-image-2.5")
        self.assertNotIn("secret-value", repr(report))
        self.assertFalse(report["secrets_exposed"])


if __name__ == "__main__":
    unittest.main()

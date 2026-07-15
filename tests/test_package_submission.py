import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package_submission.py"


class PackageSubmissionTests(unittest.TestCase):
    def test_package_contains_only_declared_files(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run"
            plans = run / "plans"
            artifacts = run / "artifacts"
            plans.mkdir(parents=True)
            artifacts.mkdir()
            (artifacts / "report.docx").write_bytes(b"docx")
            (artifacts / "secret.env").write_text("SECRET=1", encoding="utf-8")
            config = {
                "enabled": True,
                "source_root": "..",
                "allowed_output_root": "..",
                "output_zip": "../delivery/submit.zip",
                "output_folder": "../delivery/submit",
                "include_paths": [{"path": "artifacts/report.docx", "archive_root": ""}],
                "exclude_globs": ["*.env", "*.tmp", "~$*"],
                "flatten": False,
            }
            config_path = plans / "package.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--config", str(config_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output_zip = run / "delivery" / "submit.zip"
            with zipfile.ZipFile(output_zip) as archive:
                self.assertEqual(archive.namelist(), ["report.docx"])
            self.assertFalse((run / "delivery" / "submit" / "secret.env").exists())

    def test_package_rejects_output_outside_allowed_root(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run"
            plans = run / "plans"
            plans.mkdir(parents=True)
            source = run / "result.txt"
            source.write_text("result", encoding="utf-8")
            config = {
                "enabled": True,
                "source_root": "..",
                "allowed_output_root": "..",
                "output_zip": "../../outside.zip",
                "output_folder": "../delivery/submit",
                "include_paths": [{"path": "result.txt", "archive_root": ""}],
            }
            config_path = plans / "package.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--config", str(config_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must stay below allowed_output_root", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()

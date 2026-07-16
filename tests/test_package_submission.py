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
    def test_validate_plan_does_not_require_future_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run"
            plans = run / "plans"
            plans.mkdir(parents=True)
            config = {
                "enabled": False,
                "source_root": "..",
                "allowed_output_root": "..",
                "output_zip": "../delivery/submit.zip",
                "output_folder": "../delivery/submit",
                "include_paths": [
                    {"path": "future/project", "archive_root": "source", "requirement_ids": ["R1"]}
                ],
                "exclude_globs": [],
            }
            config_path = plans / "package.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--config", str(config_path), "--validate-plan"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "valid")

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
                "include_paths": [
                    {"path": "artifacts/report.docx", "archive_root": "", "requirement_ids": ["R1"]}
                ],
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
            manifest = json.loads((run / "delivery" / "submit_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["$schema"], "autoflow/package-manifest/1.0")
            self.assertTrue(manifest["overall_pass"])
            self.assertEqual(manifest["files"][0]["requirement_ids"], ["R1"])

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
                "include_paths": [
                    {"path": "result.txt", "archive_root": "", "requirement_ids": ["R1"]}
                ],
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

    def test_package_rejects_explicit_sensitive_file(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run"
            plans = run / "plans"
            plans.mkdir(parents=True)
            secret = run / ".env"
            secret.write_text("TOKEN=secret", encoding="utf-8")
            config = {
                "enabled": True,
                "source_root": "..",
                "allowed_output_root": "..",
                "output_zip": "../delivery/submit.zip",
                "output_folder": "../delivery/submit",
                "include_paths": [{"path": ".env", "archive_root": "", "requirement_ids": ["R1"]}],
                "exclude_globs": [],
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
            self.assertIn("sensitive", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()

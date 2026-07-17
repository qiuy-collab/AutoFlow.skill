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

    def test_nested_git_runtime_and_cache_files_are_recursively_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run"
            plans = run / "plans"
            project = run / "project"
            plans.mkdir(parents=True)
            (project / ".git" / "logs" / "refs" / "heads").mkdir(parents=True)
            (project / ".git" / "COMMIT_EDITMSG").write_text("secret history", encoding="utf-8")
            (project / ".git" / "logs" / "refs" / "heads" / "main").write_text("history", encoding="utf-8")
            (project / "src" / "__pycache__").mkdir(parents=True)
            (project / "src" / "__pycache__" / "app.pyc").write_bytes(b"cache")
            (project / ".venv" / "Lib").mkdir(parents=True)
            (project / ".venv" / "Lib" / "dependency.py").write_text("runtime", encoding="utf-8")
            (project / "src" / "app.py").write_text("print('ok')", encoding="utf-8")
            config = {
                "enabled": True,
                "source_root": "..",
                "allowed_output_root": "..",
                "output_zip": "../delivery/交付.zip",
                "output_folder": "../delivery/交付",
                "include_paths": [{"path": "project", "archive_root": "系统源码", "requirement_ids": ["R1"]}],
                "exclude_globs": [],
            }
            config_path = plans / "package.json"
            config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "--config", str(config_path)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(run / "delivery" / "交付.zip") as archive:
                self.assertEqual(archive.namelist(), ["系统源码/src/app.py"])
            manifest = json.loads((run / "delivery" / "交付_manifest.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(manifest["excluded"]["count"], 4)

    def test_verify_only_is_read_only_and_detects_submit_pollution(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run"
            plans = run / "plans"
            artifact = run / "artifact.txt"
            plans.mkdir(parents=True)
            artifact.write_text("final", encoding="utf-8")
            config = {
                "enabled": True,
                "source_root": "..",
                "allowed_output_root": "..",
                "output_zip": "../delivery/submit.zip",
                "output_folder": "../delivery/submit",
                "include_paths": [{"path": "artifact.txt", "archive_root": "", "requirement_ids": ["R1"]}],
            }
            config_path = plans / "package.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            built = subprocess.run([sys.executable, str(SCRIPT), "--config", str(config_path)], text=True, capture_output=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            verified = subprocess.run([sys.executable, str(SCRIPT), "--config", str(config_path), "--verify-only"], text=True, capture_output=True)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            (run / "delivery" / "submit" / "db.sqlite3").write_text("pollution", encoding="utf-8")
            polluted = subprocess.run([sys.executable, str(SCRIPT), "--config", str(config_path), "--verify-only"], text=True, capture_output=True)
            self.assertNotEqual(polluted.returncode, 0)
            self.assertIn("verification failed", polluted.stderr + polluted.stdout)


if __name__ == "__main__":
    unittest.main()

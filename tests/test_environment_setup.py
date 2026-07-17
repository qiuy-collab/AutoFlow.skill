import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "environment_setup.py"


class EnvironmentSetupTests(unittest.TestCase):
    def test_detect_reports_project_kind_without_writing_into_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "project"
            runtime = root / "runtime"
            report = root / "environment.json"
            project.mkdir()
            (project / "requirements.txt").write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "detect", "--project", str(project), "--runtime-root", str(runtime), "--report", str(report)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["$schema"], "autoflow/environment-report/1.0")
            self.assertIn("python", payload["project_kinds"])
            self.assertFalse((project / ".venv").exists())

    def test_ensure_creates_verified_python_runtime_outside_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "project"
            runtime = root / "runtime"
            report = root / "environment.json"
            project.mkdir()
            (project / "requirements.txt").write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "ensure", "--project", str(project), "--runtime-root", str(runtime), "--report", str(report), "--timeout", "120"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ready")
            self.assertTrue(Path(payload["resolved"]["python"]).is_file())
            self.assertFalse((project / ".venv").exists())
            self.assertTrue(all(item["status"] == "passed" for item in payload["checks"]))
            repeated = subprocess.run(
                [sys.executable, str(SCRIPT), "ensure", "--project", str(project), "--runtime-root", str(runtime), "--report", str(report), "--timeout", "120"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            repeated_payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertFalse(any("venv" in item["command"] for item in repeated_payload["actions"]))

    def test_runtime_root_inside_project_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            project.mkdir()
            report = Path(temp) / "report.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "detect", "--project", str(project), "--runtime-root", str(project / ".autoflow-runtime"), "--report", str(report)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "autoflow.py"


class AutoFlowCliTests(unittest.TestCase):
    def test_capabilities_reports_integrated_backends(self):
        completed = subprocess.run(
            [sys.executable, str(CLI), "capabilities", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["$schema"], "autoflow/capabilities/1.0")
        self.assertEqual(payload["capabilities"]["webapp_testing"]["backend"], "integrated-webapp-testing")
        self.assertEqual(payload["capabilities"]["superpowers"]["backend"], "integrated-superpowers")

    def test_route_returns_local_skill_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = root / "request.md"
            request.write_text("Create a project.", encoding="utf-8")
            run = root / "run"
            initialized = subprocess.run(
                [sys.executable, str(CLI), "init", "--request-file", str(request), "--output-dir", str(run), "--recipe", "project-delivery"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            routed = subprocess.run(
                [sys.executable, str(CLI), "route", "--workflow", str(run / "workflow.json"), "--step", "build", "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(routed.returncode, 0, routed.stderr)
            payload = json.loads(routed.stdout)
            self.assertEqual(payload["step"]["id"], "build")
            self.assertIn("test-driven-development", payload["skill_names"])

    def test_init_status_and_legacy_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = root / "request.md"
            request.write_text("Create a document.", encoding="utf-8")
            run = root / "run"
            completed = subprocess.run(
                [sys.executable, str(CLI), "init", "--request-file", str(request), "--output-dir", str(run), "--recipe", "document"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "initialized")

            unplanned = subprocess.run(
                [sys.executable, str(CLI), "validate", "--workflow", str(run / "workflow.json")],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(unplanned.returncode, 1)
            validation_payload = json.loads(unplanned.stdout)
            self.assertEqual(validation_payload["status"], "invalid")
            self.assertTrue(any("WORK_PLAN.md" in error for error in validation_payload["errors"]))
            self.assertTrue(any("requirement_map.json" in error for error in validation_payload["errors"]))

            status = subprocess.run(
                [sys.executable, str(CLI), "status", "--workflow", str(run / "workflow.json")],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(json.loads(status.stdout)["recipe"], "document")

            legacy = root / "legacy.json"
            legacy.write_text('{"template_path":"old.docx","output_docx":"result.docx"}', encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(CLI), "status", "--workflow", str(legacy)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("Legacy workflow detected", failed.stderr)


if __name__ == "__main__":
    unittest.main()

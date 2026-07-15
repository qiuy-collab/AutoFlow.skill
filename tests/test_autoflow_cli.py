import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "autoflow.py"


class AutoFlowCliTests(unittest.TestCase):
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

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BackendCliSmokeTests(unittest.TestCase):
    def test_backend_help_commands(self) -> None:
        scripts = (
            "artifact_map.py",
            "autoflow.py",
            "capture_frontend_screenshots.py",
            "check_images.py",
            "generate_diagram_assets.py",
            "generate_images.py",
            "package_submission.py",
            "template_adapter.py",
            "validate_prompt.py",
            "video_process.py",
        )

        for script in scripts:
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / script), "--help"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                    check=False,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"{script} --help failed:\n{result.stdout}\n{result.stderr}",
                )


if __name__ == "__main__":
    unittest.main()

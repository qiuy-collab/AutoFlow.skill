from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BackendCliSmokeTests(unittest.TestCase):
    def test_engineering_quality_adapter_routes_locally(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "engineering_quality_adapter.py"),
                "route",
                "--module",
                "task",
                "--action",
                "build",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=f"quality route failed:\n{result.stdout}\n{result.stderr}")
        self.assertIn("code-review-and-quality", result.stdout)
        self.assertIn("security-and-hardening", result.stdout)
        self.assertIn('"external_skill_required": false', result.stdout)

    def test_impeccable_adapter_check(self) -> None:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "impeccable_adapter.mjs"), "check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=f"adapter check failed:\n{result.stdout}\n{result.stderr}")
        self.assertIn("integrated-impeccable", result.stdout)

    def test_impeccable_adapter_rejects_remote_url_scans(self) -> None:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "impeccable_adapter.mjs"), "detect", "https://example.com"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("URL scans are disabled", result.stderr)

    def test_backend_help_commands(self) -> None:
        scripts = (
            "artifact_map.py",
            "autoflow.py",
            "capture_frontend_screenshots.py",
            "check_images.py",
            "generate_diagram_assets.py",
            "generate_images.py",
            "engineering_quality_adapter.py",
            "package_submission.py",
            "template_adapter.py",
            "validate_prompt.py",
            "validate_word.py",
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

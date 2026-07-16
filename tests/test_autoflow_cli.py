import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "autoflow.py"


class AutoFlowCliTests(unittest.TestCase):
    def test_integrations_command_reports_audited_catalog(self):
        completed = subprocess.run(
            [sys.executable, str(CLI), "integrations", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["$schema"], "autoflow/integrations/1.0")
        self.assertEqual(len(payload["integrations"]), 8)
        self.assertTrue(all(item["status"] == "available" for item in payload["integrations"]))

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
        self.assertEqual(payload["capabilities"]["agent_skills"]["backend"], "integrated-agent-skills")
        self.assertEqual(payload["capabilities"]["engineering_quality"]["backend"], "integrated-engineering-quality")
        self.assertEqual(payload["capabilities"]["impeccable"]["backend"], "integrated-impeccable")
        self.assertEqual(payload["capabilities"]["ppt"]["backend"], "integrated-presentation-skill")
        self.assertIn(payload["capabilities"]["ppt"]["status"], {"available", "blocked"})
        self.assertTrue(Path(payload["capabilities"]["ppt"]["skill_file"]).is_file())
        self.assertEqual(payload["capabilities"]["video"]["backend"], "integrated-video-process")
        self.assertIn(payload["capabilities"]["video"]["status"], {"available", "blocked", "missing"})
        self.assertTrue(Path(payload["capabilities"]["video"]["script"]).is_file())
        self.assertEqual(payload["capabilities"]["image"]["backend"], "integrated-image-assets")
        self.assertIn(payload["capabilities"]["image"]["status"], {"available", "blocked", "missing"})

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
            self.assertIn("code-review-and-quality", payload["skill_names"])
            self.assertIn("api-and-interface-design", payload["skill_names"])
            self.assertIn("frontend-ui-engineering", payload["skill_names"])
            self.assertIn("agent_skills", payload["capability_names"])
            self.assertTrue(all(Path(path).is_file() for path in payload["skill_files"]))

    def test_ppt_route_returns_integrated_local_capability_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = root / "request.md"
            request.write_text("Create a defense presentation.", encoding="utf-8")
            run = root / "run"
            initialized = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "init",
                    "--request-file",
                    str(request),
                    "--output-dir",
                    str(run),
                    "--recipe",
                    "presentation",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            routed = subprocess.run(
                [sys.executable, str(CLI), "route", "--workflow", str(run / "workflow.json"), "--step", "ppt", "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(routed.returncode, 0, routed.stderr)
            payload = json.loads(routed.stdout)
            self.assertIn("ppt", payload["capability_names"])
            self.assertEqual(payload["capabilities"]["ppt"]["backend"], "integrated-presentation-skill")
            self.assertTrue(all(Path(path).is_file() for path in payload["capability_files"]))

    def test_auto_init_records_a_compound_recipe_recommendation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = root / "request.md"
            request.write_text("学生管理系统源码、论文和答辩PPT", encoding="utf-8")
            run = root / "run"
            initialized = subprocess.run(
                [sys.executable, str(CLI), "init", "--request-file", str(request), "--output-dir", str(run), "--recipe", "auto"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            workflow = json.loads((run / "workflow.json").read_text(encoding="utf-8"))
            self.assertEqual(workflow["recipe"], "project-report-and-slides")
            self.assertEqual(workflow["recipe_selection"]["selected"], "project-report-and-slides")
            self.assertEqual([step["id"] for step in workflow["steps"]], ["source", "build", "image", "word", "ppt", "package"])

    def test_student_management_delivery_smoke_keeps_plan_stop_and_routes_every_step(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = root / "request.md"
            request.write_text(
                "学生管理系统：交付可运行源码、论文和答辩PPT；先搜索GitHub候选，用户选择后再改造。",
                encoding="utf-8",
            )
            run = root / "run"
            initialized = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "init",
                    "--request-file",
                    str(request),
                    "--output-dir",
                    str(run),
                    "--recipe",
                    "auto",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            workflow = json.loads((run / "workflow.json").read_text(encoding="utf-8"))
            state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
            self.assertEqual(workflow["recipe"], "project-report-and-slides")
            self.assertTrue(state["gates"]["plan"]["active"])
            self.assertEqual(state["gates"]["plan"]["status"], "pending")
            self.assertEqual(state["gates"]["source"]["status"], "not_applicable")

            for step in workflow["steps"]:
                routed = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "route",
                        "--workflow",
                        str(run / "workflow.json"),
                        "--step",
                        step["id"],
                        "--json",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(routed.returncode, 0, routed.stderr)
                payload = json.loads(routed.stdout)
                self.assertEqual(payload["step"]["id"], step["id"])
                self.assertTrue(payload["skill_names"])
                self.assertTrue(all(Path(path).is_file() for path in payload["skill_files"]))

            next_state = subprocess.run(
                [sys.executable, str(CLI), "next", "--workflow", str(run / "workflow.json")],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(next_state.returncode, 0, next_state.stderr)
            self.assertEqual(json.loads(next_state.stdout)["ready_steps"], [])

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

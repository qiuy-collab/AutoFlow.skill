import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autoflow_core import (  # noqa: E402
    AutoFlowError,
    approve_gate,
    detect_ppt_backend,
    detect_word_backend,
    initialize_run,
    load_json,
    load_run,
    refresh_ready,
    save_json,
    save_run,
    set_gate_state,
    sync_planning_state,
    transition_step,
    validate_run,
    validate_workflow_definition,
)


COMPLETE_PLAN = """# Work Plan

## 目标
完成用户要求的真实产物，并用可复现验证证明结果满足要求。这里补充足够的目标说明，避免模板被误认为已经完成。

## 工作流
先执行任务模块，再生成或捕获证据，然后装配目标文档或交付包。所有依赖、STOP 和验证都记录在 AutoFlow 状态文件中。

## 产物
产出 workflow 声明的全部文件、目录或压缩包；每个产物都有绝对路径、生产步骤、消费者和 SHA-256。

## 范围与约束
不制造虚假证据，不跳过用户批准，不把未声明的缓存或敏感文件装入交付包，所有测试只在临时目录运行。
"""


class AutoFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.request = self.root / "request.md"
        self.request.write_text("Build the requested deliverables.", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def init(self, recipe):
        workflow_path = initialize_run(self.request, self.root / "run", recipe)
        workflow, state, manifest, paths = load_run(workflow_path)
        paths["work_plan"].write_text(COMPLETE_PLAN, encoding="utf-8")
        approve_gate(workflow, state, manifest, paths, "plan", "User approved the complete work plan")
        save_run(state, manifest, paths)
        return workflow_path, workflow, state, manifest, paths

    def make_artifact(self, name, content="artifact"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def complete_step(self, workflow, state, manifest, paths, step_id, artifacts):
        refresh_ready(workflow, state)
        transition_step(workflow, state, manifest, paths, step_id, "running", "started", {})
        transition_step(workflow, state, manifest, paths, step_id, "completed", "verified", artifacts)

    def test_word_only_recipe_can_finish_and_requires_delivery_stop(self):
        _, workflow, state, manifest, paths = self.init("document")
        refresh_ready(workflow, state)
        transition_step(workflow, state, manifest, paths, "task", "skipped", "Not needed", {})
        transition_step(workflow, state, manifest, paths, "image", "skipped", "Not needed", {})
        docx = self.make_artifact("result.docx")
        self.complete_step(workflow, state, manifest, paths, "word", {"word.document": docx})
        self.assertTrue(state["gates"]["delivery"]["active"])
        self.assertEqual(state["gates"]["delivery"]["status"], "pending")
        approve_gate(workflow, state, manifest, paths, "delivery", "User accepted the Word delivery")
        self.assertEqual(state["status"], "completed")

    def test_visual_stop_blocks_word_until_user_approval(self):
        _, workflow, state, manifest, paths = self.init("lab-report")
        task_result = self.make_artifact("task-result.json", "{}")
        self.complete_step(workflow, state, manifest, paths, "task", {"task.result": task_result})
        image_dir = self.root / "images"
        image_dir.mkdir()
        (image_dir / "screen.png").write_bytes(b"png")
        self.complete_step(workflow, state, manifest, paths, "image", {"image.assets": image_dir})
        self.assertEqual(refresh_ready(workflow, state), [])
        self.assertEqual(state["gates"]["visual"]["status"], "pending")
        approve_gate(workflow, state, manifest, paths, "visual", "User approved the displayed screenshots")
        self.assertIn("word", refresh_ready(workflow, state))

    def test_github_candidates_activate_source_stop(self):
        _, workflow, state, manifest, paths = self.init("project-delivery")
        refresh_ready(workflow, state)
        transition_step(workflow, state, manifest, paths, "source", "running", "searching", {})
        source_plan = {
            "status": "awaiting_user_choice",
            "queries": ["course system servlet jdbc"],
            "candidates": [
                {
                    "rank": rank,
                    "name": name,
                    "repository_url": f"https://github.com/{name}",
                    "revision": revision,
                    "license": "MIT",
                    "scores": {
                        "requirement_fit": 6 - rank,
                        "modification_distance": 4,
                        "stack": 5,
                        "buildability": 4,
                        "maintenance": 4,
                        "license": 5,
                    },
                    "judgment": "Usable fit with a buildable baseline",
                }
                for rank, name, revision in (
                    (1, "owner/repo", "abc123"),
                    (2, "owner/runner-up", "def456"),
                    (3, "owner/third-choice", "ghi789"),
                )
            ],
            "selected_candidate": {},
            "user_choice": {"status": "awaiting_user_choice"},
            "fallback": {"used": False, "reason": ""},
        }
        save_json(paths["source_plan"], source_plan)
        transition_step(
            workflow,
            state,
            manifest,
            paths,
            "source",
            "completed",
            "candidates inspected",
            {"source.plan": paths["source_plan"]},
        )
        self.assertEqual(state["gates"]["source"]["status"], "pending")
        self.assertEqual(refresh_ready(workflow, state), [])

        source_plan.update(
            {
                "status": "selected",
                "selected_candidate": {
                    "name": "owner/repo",
                    "repository_url": "https://github.com/owner/repo",
                    "selected_revision": "abc123",
                    "selection_rationale": "Best requirement fit",
                },
                "user_choice": {"status": "confirmed", "selected_rank": 1},
            }
        )
        save_json(paths["source_plan"], source_plan)
        approve_gate(workflow, state, manifest, paths, "source", "User selected candidate 1")
        self.assertIn("build", refresh_ready(workflow, state))
        self.assertEqual(validate_run(workflow, state, manifest, paths), [])

    def test_no_candidate_uses_from_scratch_without_source_approval(self):
        _, workflow, state, manifest, paths = self.init("project-delivery")
        refresh_ready(workflow, state)
        transition_step(workflow, state, manifest, paths, "source", "running", "searching", {})
        source_plan = {
            "status": "no_suitable_project",
            "queries": ["very specific unsupported stack"],
            "candidates": [],
            "rejected_candidates": [{"repository_url": "https://github.com/owner/repo", "reason": "Wrong stack"}],
            "fallback": {"used": True, "reason": "No candidate satisfies the required stack and license"},
        }
        save_json(paths["source_plan"], source_plan)
        transition_step(
            workflow,
            state,
            manifest,
            paths,
            "source",
            "completed",
            "no suitable source",
            {"source.plan": paths["source_plan"]},
        )
        self.assertEqual(state["gates"]["source"]["status"], "not_applicable")
        self.assertIn("build", refresh_ready(workflow, state))

    def test_missing_artifact_rejects_completion(self):
        _, workflow, state, manifest, paths = self.init("custom")
        refresh_ready(workflow, state)
        transition_step(workflow, state, manifest, paths, "task", "running", "started", {})
        with self.assertRaises(AutoFlowError):
            transition_step(workflow, state, manifest, paths, "task", "completed", "done", {})

    def test_source_gate_cannot_be_skipped_without_no_candidate_record(self):
        _, workflow, state, _, paths = self.init("project-delivery")
        with self.assertRaises(AutoFlowError):
            set_gate_state(workflow, state, paths, "source", "not_applicable", "skip")

    def test_build_completion_rejects_placeholder_project(self):
        _, workflow, state, manifest, paths = self.init("project-delivery")
        refresh_ready(workflow, state)
        transition_step(workflow, state, manifest, paths, "source", "running", "searching", {})
        source_plan = {
            "status": "no_suitable_project",
            "queries": ["specific project"],
            "candidates": [],
            "fallback": {"used": True, "reason": "No compatible licensed repository"},
            "search_notes": "Search results did not contain a compatible repository.",
        }
        save_json(paths["source_plan"], source_plan)
        transition_step(
            workflow, state, manifest, paths, "source", "completed", "searched",
            {"source.plan": paths["source_plan"]},
        )
        refresh_ready(workflow, state)
        transition_step(workflow, state, manifest, paths, "build", "running", "building", {})
        project = self.root / "placeholder-project"
        project.mkdir()
        result = self.make_artifact("placeholder-result.json", "{}")
        with self.assertRaisesRegex(AutoFlowError, "empty|README|source_mode"):
            transition_step(
                workflow, state, manifest, paths, "build", "completed", "done",
                {"project.source": project, "task.result": result},
            )

    def test_cycle_is_rejected(self):
        workflow_path = initialize_run(self.request, self.root / "cycle", "custom")
        workflow = load_json(workflow_path)
        workflow["steps"][0]["needs"] = ["task"]
        with self.assertRaisesRegex(AutoFlowError, "cannot depend on itself|cycle"):
            validate_workflow_definition(workflow)

    def test_custom_dag_can_sync_before_plan_only(self):
        workflow_path = initialize_run(self.request, self.root / "sync", "custom")
        workflow, state, manifest, paths = load_run(workflow_path)
        workflow["steps"].append(
            {
                "id": "package",
                "module": "package",
                "action": "assemble",
                "needs": ["task"],
                "inputs": ["task.result"],
                "outputs": ["package.bundle"],
                "validator": "artifacts_exist",
            }
        )
        sync_planning_state(workflow, state)
        self.assertEqual(set(state["steps"]), {"task", "package"})
        paths["work_plan"].write_text(COMPLETE_PLAN, encoding="utf-8")
        approve_gate(workflow, state, manifest, paths, "plan", "User approved the custom DAG")
        with self.assertRaises(AutoFlowError):
            sync_planning_state(workflow, state)

    def test_sync_populates_capabilities_for_custom_word_and_ppt_steps(self):
        workflow_path = initialize_run(self.request, self.root / "capabilities", "custom")
        workflow, state, _, _ = load_run(workflow_path)
        workflow["steps"] = [
            {
                "id": "word",
                "module": "word",
                "action": "create",
                "needs": [],
                "inputs": ["request"],
                "outputs": ["word.document"],
                "validator": "artifacts_exist",
            },
            {
                "id": "ppt",
                "module": "ppt",
                "action": "create",
                "needs": [],
                "inputs": ["request"],
                "outputs": ["ppt.presentation"],
                "validator": "artifacts_exist",
                "gate_after": "visual",
            },
        ]
        sync_planning_state(workflow, state)
        self.assertEqual(workflow["capabilities"]["word"]["status"], "available")
        self.assertEqual(workflow["capabilities"]["ppt"]["status"], "available")

    def test_legacy_workflow_is_rejected(self):
        run = self.root / "legacy"
        run.mkdir()
        legacy = run / "workflow.json"
        legacy.write_text(json.dumps({"template_path": "old.docx", "output_docx": "result.docx"}), encoding="utf-8")
        with self.assertRaisesRegex(AutoFlowError, "Legacy workflow detected"):
            load_run(legacy)

    def test_registered_artifact_change_fails_validation(self):
        _, workflow, state, manifest, paths = self.init("custom")
        artifact = self.make_artifact("result.txt", "v1")
        self.complete_step(workflow, state, manifest, paths, "task", {"task.result": artifact})
        artifact.write_text("v2", encoding="utf-8")
        errors = validate_run(workflow, state, manifest, paths)
        self.assertTrue(any("changed after validation" in error for error in errors))

    def test_ppt_recipe_discovers_external_skill_backend(self):
        backend = detect_ppt_backend()
        self.assertEqual(backend["status"], "available")
        self.assertTrue(Path(backend["skill_file"]).is_file())
        workflow_path = initialize_run(self.request, self.root / "slides", "presentation")
        workflow = load_json(workflow_path)
        self.assertEqual(workflow["capabilities"]["ppt"]["status"], "available")

    def test_word_recipe_discovers_external_skill_backend(self):
        backend = detect_word_backend()
        self.assertEqual(backend["status"], "available")
        self.assertTrue(Path(backend["skill_file"]).is_file())
        workflow_path = initialize_run(self.request, self.root / "word", "document")
        workflow = load_json(workflow_path)
        self.assertEqual(workflow["capabilities"]["word"]["status"], "available")


if __name__ == "__main__":
    unittest.main()

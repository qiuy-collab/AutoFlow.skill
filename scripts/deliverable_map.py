"""
Deliverable map for auto-lab.

Returns a structured map of all expected deliverables for a given workflow run.
Used by the agent during delivery review (Step 18) to verify nothing is missing.

Also provides a CLI entrypoint for quick checks.

Usage:
    # Print deliverable map
    python deliverable_map.py --workflow workflow.json

    # Check all deliverables exist
    python deliverable_map.py --workflow workflow.json --check
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional


DELIVERABLE_SPEC = {
    # ── Planning & Configuration ──
    "WORK_PLAN.md": {
        "category": "planning",
        "description": "Agent-authored work plan with requirement summary, scoring mapping, scope, substitutions, and task checklist",
        "created_by": "agent (Step 4)",
        "optional": False,
    },
    "requirement_checklist.json": {
        "category": "planning",
        "description": "Machine-readable checklist of enabled routes and features",
        "created_by": "init_run.py",
        "optional": False,
    },
    "pre_task_plan.json": {
        "category": "planning",
        "description": "Pre-task execution plan (only if pre_task_required=true)",
        "created_by": "init_run.py",
        "optional": True,
    },
    "copywriting.md": {
        "category": "planning",
        "description": "Report body content (Markdown)",
        "created_by": "agent (Step 9)",
        "optional": False,
    },
    "prompt_config.json": {
        "category": "planning",
        "description": "AI image generation configuration (txt2img and/or img2img)",
        "created_by": "agent (Step 9)",
        "optional_if": "ai_images_required=false",
    },
    "browser_capture_plan.json": {
        "category": "planning",
        "description": "Browser screenshot capture plan",
        "created_by": "agent (Step 9)",
        "optional_if": "browser_capture_required=false",
    },
    "diagram_plan.json": {
        "category": "planning",
        "description": "Diagram generation plan",
        "created_by": "agent (Step 9)",
        "optional_if": "diagram_assets_required=false",
    },
    "video_plan.json": {
        "category": "planning",
        "description": "Video processing plan",
        "created_by": "agent (Step 9)",
        "optional_if": "video_required=false",
    },
    "reference_template_cleanup.json": {
        "category": "planning",
        "description": "Template cleanup instructions",
        "created_by": "agent (Step 9)",
        "optional": False,
    },
    "submission_package.json": {
        "category": "planning",
        "description": "Submission package manifest",
        "created_by": "agent (Step 9)",
        "optional_if": "submission_package_required=false",
    },
    "insert_config.json": {
        "category": "planning",
        "description": "Image insertion configuration for DOCX",
        "created_by": "agent (Step 9)",
        "optional": False,
    },

    # ── Generated Assets ──
    "output/generated_images/": {
        "category": "assets",
        "description": "AI-generated images (txt2img and/or img2img output)",
        "created_by": "generate_images.py",
        "optional_if": "ai_images_required=false",
    },
    "image_generation_report.json": {
        "category": "assets",
        "description": "Per-image generation report including method (txt2img / img2img), upstream, duration, and status",
        "created_by": "generate_images.py",
        "optional_if": "ai_images_required=false",
    },
    "output/browser_captures/": {
        "category": "assets",
        "description": "Browser-captured screenshots",
        "created_by": "agent",
        "optional_if": "browser_capture_required=false",
    },
    "output/diagrams/": {
        "category": "assets",
        "description": "Generated diagram files (PNG/SVG)",
        "created_by": "agent",
        "optional_if": "diagram_assets_required=false",
    },
    "output/video_frames/": {
        "category": "assets",
        "description": "Extracted video frames",
        "created_by": "agent",
        "optional_if": "video_required=false",
    },

    # ── Report Output ──
    "result.docx": {
        "category": "report",
        "description": "Final filled DOCX report (uses the --output-docx-name from init_run)",
        "created_by": "fill_template.py",
        "optional": False,
    },

    # ── Submission ──
    "submit/": {
        "category": "submission",
        "description": "Submission folder with all required deliverable files",
        "created_by": "agent",
        "optional_if": "submission_package_required=false",
    },
    "submit.zip": {
        "category": "submission",
        "description": "Submission archive (compressed submit/ folder)",
        "created_by": "agent",
        "optional_if": "submission_package_required=false",
    },

    # ── Quality & Review ──
    "delivery_review.json": {
        "category": "review",
        "description": "Final acceptance record — every deliverable checked",
        "created_by": "agent (Step 18)",
        "optional": False,
    },
    "prompt_validation_report.json": {
        "category": "review",
        "description": "Validation report from validate_prompt.py (three-layer: structure / requirement / consistency)",
        "created_by": "validate_prompt.py",
        "optional_if": "ai_images_required=false",
    },

    # ── Execution ──
    "workflow.json": {
        "category": "execution",
        "description": "Run configuration written by init_run.py",
        "created_by": "init_run.py",
        "optional": False,
    },
    "template_manifest.json": {
        "category": "execution",
        "description": "Template structure analysis",
        "created_by": "init_run.py",
        "optional": False,
    },
}


def normalize_docx_name(run_dir: Path, workflow: Optional[dict] = None) -> str:
    """Find the expected DOCX output name from workflow.json or fall back to 'result.docx'."""
    if workflow and workflow.get("output_docx_name"):
        return workflow["output_docx_name"]
    # Try reading from workflow.json in the run directory
    wf_path = run_dir / "workflow.json"
    if wf_path.exists():
        try:
            wf = json.loads(wf_path.read_text(encoding="utf-8"))
            if wf.get("output_docx_name"):
                return wf["output_docx_name"]
        except Exception:
            pass
    return "result.docx"


def build_deliverable_map(run_dir: Path, checklist: Optional[dict] = None) -> List[Dict]:
    """Build the deliverable map for a given run directory.

    Returns a list of dicts: {path, category, description, optional, exists, status}
    """
    if checklist is None:
        ck_path = run_dir / "requirement_checklist.json"
        if ck_path.exists():
            checklist = json.loads(ck_path.read_text(encoding="utf-8"))
        else:
            checklist = {}

    workflow = None
    wf_path = run_dir / "workflow.json"
    if wf_path.exists():
        try:
            workflow = json.loads(wf_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    docx_name = normalize_docx_name(run_dir, workflow)

    results = []
    for path, spec in DELIVERABLE_SPEC.items():
        # Decide if this deliverable is required
        optional = spec.get("optional", False)
        if not optional and "optional_if" in spec:
            flag_key = spec["optional_if"]
            required = not checklist.get(flag_key, True)
            optional = not required

        # Substitute docx name
        resolved_path = path
        if path == "result.docx":
            resolved_path = docx_name

        full_path = run_dir / resolved_path

        # Check existence (directories must contain at least 1 file)
        if resolved_path.endswith("/"):
            exists = full_path.is_dir() and any(full_path.iterdir())
        else:
            exists = full_path.exists()

        results.append({
            "path": resolved_path,
            "full_path": str(full_path),
            "category": spec["category"],
            "description": spec["description"],
            "created_by": spec["created_by"],
            "optional": optional,
            "exists": exists,
            "status": "present" if exists else ("optional" if optional else "missing"),
        })

    return results


def print_deliverable_map(deliverables: List[Dict]):
    """Print a formatted deliverable map to stdout."""
    categories = {}
    for d in deliverables:
        cat = d["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(d)

    cat_labels = {
        "planning": "📋 Planning & Configuration",
        "assets": "🎨 Generated Assets",
        "report": "📄 Report Output",
        "submission": "📦 Submission",
        "review": "✅ Quality & Review",
        "execution": "⚙️ Execution",
    }

    for cat in ["planning", "assets", "report", "submission", "review", "execution"]:
        items = categories.get(cat, [])
        if not items:
            continue
        print(f"\n{cat_labels.get(cat, cat)}")
        for d in items:
            icon = "✅" if d["exists"] else ("🟡" if d["optional"] else "❌")
            optional_tag = " (optional)" if d["optional"] else ""
            method_tag = f" [{d['created_by']}]"
            print(f"  {icon} {d['path']}{optional_tag}{method_tag}")
            if d["status"] == "missing":
                print(f"      ⚠️  MISSING: {d['description']}")


def check_all_exist(deliverables: List[Dict]) -> bool:
    """Return True if all non-optional deliverables exist."""
    all_ok = True
    for d in deliverables:
        if not d["optional"] and not d["exists"]:
            all_ok = False
    return all_ok


def parse_args():
    parser = argparse.ArgumentParser(
        description="Deliverable map for auto-lab runs.",
        epilog="Examples:\n  python deliverable_map.py --workflow workflow.json\n  python deliverable_map.py --workflow workflow.json --check"
    )
    parser.add_argument("--workflow", "-w", required=True, help="Path to workflow.json or the run directory")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if any non-optional deliverable is missing")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Output JSON instead of formatted text")
    return parser.parse_args()


def main():
    args = parse_args()
    run_dir = Path(args.workflow).expanduser().resolve()
    if run_dir.is_file():
        run_dir = run_dir.parent

    deliverables = build_deliverable_map(run_dir)

    if args.json_output:
        print(json.dumps(deliverables, ensure_ascii=False, indent=2))
    else:
        print_deliverable_map(deliverables)

    if args.check:
        all_ok = check_all_exist(deliverables)
        if all_ok:
            print("\n✅ All required deliverables present.")
            sys.exit(0)
        else:
            print("\n❌ Some required deliverables are missing.")
            sys.exit(1)


if __name__ == "__main__":
    main()

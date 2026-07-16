import argparse
import json
import sys
from pathlib import Path

from autoflow_core import (
    AutoFlowError,
    detect_agent_skills_backend,
    approve_gate,
    detect_engineering_quality_backend,
    detect_impeccable_backend,
    detect_ppt_backend,
    detect_superpowers_backend,
    detect_webapp_testing_backend,
    detect_word_backend,
    integration_catalog,
    initialize_run,
    load_run,
    parse_artifact_specs,
    refresh_ready,
    route_for_workflow,
    save_json,
    save_run,
    set_gate_state,
    status_summary,
    sync_planning_state,
    transition_step,
    validate_run,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Initialize, validate, and advance an AutoFlow workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a new AutoFlow run directory")
    init.add_argument("--request-file", required=True)
    init.add_argument("--output-dir", required=True)
    init.add_argument("--recipe", default="auto")

    for name in ("validate", "status", "next", "sync"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--workflow", required=True)

    capabilities = subparsers.add_parser("capabilities", help="Inspect integrated and optional module backends")
    capabilities.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    integrations = subparsers.add_parser("integrations", help="List and audit checked-in integrations")
    integrations.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    route = subparsers.add_parser("route", help="Resolve local module and methodology Skills for a workflow step")
    route.add_argument("--workflow", required=True)
    route.add_argument("--step", default="")
    route.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    transition = subparsers.add_parser("transition", help="Advance one workflow step")
    transition.add_argument("--workflow", required=True)
    transition.add_argument("--step", required=True)
    transition.add_argument("--to", required=True, choices=["running", "blocked", "completed", "failed", "skipped"])
    transition.add_argument("--note", default="")
    transition.add_argument("--artifact", action="append", default=[], metavar="ARTIFACT_ID=PATH")

    approve = subparsers.add_parser("approve", help="Record explicit user approval for a STOP gate")
    approve.add_argument("--workflow", required=True)
    approve.add_argument("--gate", required=True, choices=["plan", "source", "visual", "delivery"])
    approve.add_argument("--note", required=True)

    gate = subparsers.add_parser("gate", help="Reject or mark a conditional STOP as not applicable")
    gate.add_argument("--workflow", required=True)
    gate.add_argument("--gate", required=True, choices=["plan", "source", "visual", "delivery"])
    gate.add_argument("--to", required=True, choices=["rejected", "not_applicable"])
    gate.add_argument("--note", required=True)
    return parser.parse_args()


def emit(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    try:
        if args.command == "init":
            path = initialize_run(Path(args.request_file), Path(args.output_dir), args.recipe)
            emit({"status": "initialized", "workflow": str(path)})
            return 0
        if args.command == "capabilities":
            payload = {
                "$schema": "autoflow/capabilities/1.0",
                    "capabilities": {
                    "word": detect_word_backend(),
                    "webapp_testing": detect_webapp_testing_backend(),
                    "superpowers": detect_superpowers_backend(),
                    "agent_skills": detect_agent_skills_backend(),
                    "engineering_quality": detect_engineering_quality_backend(),
                    "impeccable": detect_impeccable_backend(),
                    "ppt": detect_ppt_backend(),
                },
            }
            if args.json:
                emit(payload)
            else:
                for name, capability in payload["capabilities"].items():
                    backend = capability.get("backend") or "not configured"
                    print(f"{name}: {capability.get('status', 'unknown')} ({backend})")
            return 0
        if args.command == "integrations":
            payload = {"$schema": "autoflow/integrations/1.0", "integrations": integration_catalog()}
            if args.json:
                emit(payload)
            else:
                for item in payload["integrations"]:
                    print(f"{item['name']}: {item['status']} ({item.get('license', 'unknown')})")
            return 0

        workflow, state, manifest, paths = load_run(Path(args.workflow))
        if args.command == "route":
            payload = route_for_workflow(workflow, state, args.step or None)
            if args.json:
                emit(payload)
            else:
                for item in payload.get("steps", [payload.get("step", payload)]):
                    print(f"{item['id']}: {item['module']}.{item['action']}")
                    print(f"  module: {item['module_file']}")
                    print(f"  skills: {', '.join(item['skill_names'])}")
                    for path in item["skill_files"]:
                        print(f"    - {path}")
            return 0
        if args.command == "validate":
            errors = validate_run(workflow, state, manifest, paths)
            if errors:
                emit({"status": "invalid", "errors": errors})
                return 1
            emit({"status": "valid", "workflow": str(paths["workflow"])})
            return 0
        if args.command == "status":
            emit(status_summary(workflow, state, manifest))
            return 0
        if args.command == "next":
            ready = refresh_ready(workflow, state)
            save_run(state, manifest, paths)
            emit({"ready_steps": ready, "state": status_summary(workflow, state, manifest)})
            return 0
        if args.command == "sync":
            sync_planning_state(workflow, state)
            save_json(paths["workflow"], workflow)
            save_run(state, manifest, paths)
            emit({"status": "synchronized", "state": status_summary(workflow, state, manifest)})
            return 0
        if args.command == "transition":
            artifacts = parse_artifact_specs(args.artifact)
            transition_step(workflow, state, manifest, paths, args.step, args.to, args.note, artifacts)
            save_run(state, manifest, paths)
            emit(status_summary(workflow, state, manifest))
            return 0
        if args.command == "approve":
            approve_gate(workflow, state, manifest, paths, args.gate, args.note)
            if args.gate == "plan":
                save_json(paths["workflow"], workflow)
            save_run(state, manifest, paths)
            emit(status_summary(workflow, state, manifest))
            return 0
        if args.command == "gate":
            set_gate_state(workflow, state, paths, args.gate, args.to, args.note)
            save_run(state, manifest, paths)
            emit(status_summary(workflow, state, manifest))
            return 0
        raise AutoFlowError(f"Unsupported command: {args.command}")
    except AutoFlowError as exc:
        print(f"AutoFlow error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

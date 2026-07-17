import argparse
import json
from pathlib import Path

from autoflow_core import load_run, validate_run


def parse_args():
    parser = argparse.ArgumentParser(description="Display and verify an AutoFlow artifact manifest.")
    parser.add_argument("--workflow", required=True, help="Path to workflow.json")
    parser.add_argument("--check", action="store_true", help="Exit non-zero when the run or an artifact is invalid")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit machine-readable JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    workflow, state, manifest, paths = load_run(Path(args.workflow))
    errors = validate_run(workflow, state, manifest, paths)
    artifacts = [
        {
            "id": item["id"],
            "type": item["type"],
            "path": item["path"],
            "producer": item["producer"],
            "consumers": item.get("consumers", []),
            "sha256": item["sha256"],
            "valid": not any(item["id"] in error for error in errors),
        }
        for item in manifest.get("artifacts", [])
    ]
    payload = {
        "workflow_id": workflow["workflow_id"],
        "run_status": state["status"],
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "errors": errors,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"AutoFlow artifacts: {len(artifacts)} | run status: {state['status']}")
        for item in artifacts:
            marker = "OK" if item["valid"] else "FAIL"
            print(f"[{marker}] {item['id']} ({item['type']}) -> {item['path']}")
        for error in errors:
            print(f"[ERROR] {error}")
    if args.check and errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

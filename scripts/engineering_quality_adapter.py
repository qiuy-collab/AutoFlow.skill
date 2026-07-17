#!/usr/bin/env python3
"""Resolve AutoFlow's local engineering-quality guidance without networking."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoflow_core import (  # noqa: E402
    detect_engineering_quality_backend,
    engineering_quality_skill_names,
)


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve AutoFlow's local engineering-quality integration.")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check")
    check.add_argument("--json", action="store_true")

    route = sub.add_parser("route")
    route.add_argument("--module", required=True)
    route.add_argument("--action", required=True)
    route.add_argument("--status", default="pending")
    route.add_argument("--json", action="store_true")

    args = parser.parse_args()
    backend = detect_engineering_quality_backend()
    if args.command == "check":
        payload = {
            "$schema": "autoflow/engineering-quality/1.0",
            "capability": backend,
        }
        if args.json:
            emit(payload)
        else:
            print(f"engineering-quality: {backend['status']} ({backend['backend']})")
        return 0 if backend["status"] == "available" else 1

    names = engineering_quality_skill_names(
        {"module": args.module, "action": args.action}, args.status
    )
    files = backend.get("skill_files", {})
    payload = {
        "$schema": "autoflow/engineering-quality-route/1.0",
        "module": args.module,
        "action": args.action,
        "status": args.status,
        "skill_names": names,
        "skill_files": [files.get(name, "") for name in names],
        "capability": backend,
    }
    if args.json:
        emit(payload)
    else:
        print(f"{args.module}.{args.action}: {', '.join(names) or 'no engineering-quality route'}")
        for path in payload["skill_files"]:
            print(f"  - {path}")
    return 0 if backend["status"] == "available" or not names else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check local availability of the impeccable package.

Output (JSON on stdout): {"status": "available"|"missing"|"blocked", "version": ...}
"""
import json
import pathlib
import shutil
import subprocess
import sys


def main() -> int:
    node = shutil.which("node")
    if not node:
        print(json.dumps({"status": "missing", "version": None, "error": "Node.js not found in PATH"}))
        return 0
    base = pathlib.Path(__file__).resolve().parent.parent
    required = (
        base / "SKILL.md",
        base / "scripts" / "impeccable_adapter.mjs",
        base / "scripts" / "detect.mjs",
        base / "scripts" / "context.mjs",
        base / "scripts" / "context-signals.mjs",
        base / "scripts" / "palette.mjs",
        base / "scripts" / "command-metadata.json",
    )
    missing = [str(p.relative_to(base)) for p in required if not p.is_file()]
    if missing:
        print(json.dumps({"status": "missing", "version": None, "error": f"Missing package files: {', '.join(missing)}"}))
        return 0
    try:
        result = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10)
    except Exception as exc:  # pragma: no cover - subprocess failure path
        print(json.dumps({"status": "blocked", "version": None, "error": str(exc)}))
        return 0
    node_version = (result.stdout or result.stderr or "").strip() or "unknown"
    print(json.dumps({"status": "available" if result.returncode == 0 else "blocked", "version": f"node={node_version}"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

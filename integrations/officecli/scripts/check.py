#!/usr/bin/env python3
"""Check local availability of the officecli binary.

Output (JSON on stdout): {"status": "available"|"missing"|"blocked", "version": ...}
"""
import json
import shutil
import subprocess
import sys


def main() -> int:
    exe = shutil.which("officecli")
    if not exe:
        print(json.dumps({"status": "missing", "version": None, "error": "officecli binary not found in PATH"}))
        return 0
    try:
        result = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10)
    except Exception as exc:  # pragma: no cover - subprocess failure path
        print(json.dumps({"status": "blocked", "version": None, "error": str(exc)}))
        return 0
    version = (result.stdout or result.stderr or "").strip() or "unknown"
    print(json.dumps({"status": "available" if result.returncode == 0 else "blocked", "version": version}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

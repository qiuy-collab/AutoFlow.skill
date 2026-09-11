"""Check the checked-in minimax-docx package and .NET runtime."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "scripts" / "dotnet" / "MiniMaxAIDocx.Cli"


def main() -> int:
    if not (ROOT / "SKILL.md").is_file() or not PROJECT.is_dir():
        print(json.dumps({"status": "blocked", "version": None, "error": "minimax-docx package is incomplete"}))
        return 0
    dotnet = shutil.which("dotnet")
    if not dotnet:
        print(json.dumps({"status": "missing", "version": None, "error": "dotnet runtime not found in PATH"}))
        return 0
    try:
        result = subprocess.run([dotnet, "--version"], capture_output=True, text=True, timeout=30)
    except Exception as exc:
        print(json.dumps({"status": "blocked", "version": None, "error": str(exc)}))
        return 0
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "dotnet --version failed").strip()
        print(json.dumps({"status": "blocked", "version": None, "error": error}))
        return 0
    print(json.dumps({"status": "available", "version": result.stdout.strip(), "error": None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

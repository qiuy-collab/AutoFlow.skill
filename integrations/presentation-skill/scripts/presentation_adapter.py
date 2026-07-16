#!/usr/bin/env python3
"""Offline AutoFlow adapter for the curated presentation-skill surface."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts" / "build_deck_pptxgenjs.js"
QA = ROOT / "scripts" / "qa_gate.py"
INVENTORY = ROOT / "scripts" / "inventory.py"
EXTRACT = ROOT / "scripts" / "extract_outline.py"


def _node_module_candidates() -> list[Path]:
    values = []
    configured = os.environ.get("PPTX_NODE_MODULES", "").strip()
    if configured:
        values.append(Path(configured).expanduser())
    values.extend(
        [
            ROOT / "node_modules",
            Path.cwd() / "node_modules",
            Path.home() / "codex" / "CascadeProjects" / "pptx_ab_comparison" / "node_modules",
        ]
    )
    return list(dict.fromkeys(values))


def _node_can_resolve(module: str) -> tuple[bool, str]:
    node = shutil.which("node")
    if not node:
        return False, "Node.js executable not found"
    paths = [str(path) for path in _node_module_candidates() if path.is_dir()]
    env = os.environ.copy()
    if paths:
        env["NODE_PATH"] = os.pathsep.join(paths + [env.get("NODE_PATH", "")]).strip(os.pathsep)
    probe = subprocess.run(
        [node, "-e", f"require.resolve({module!r})"],
        env=env,
        capture_output=True,
        text=True,
    )
    if probe.returncode:
        return False, f'Node module "{module}" is not resolvable'
    return True, probe.stdout.strip()


def capability_report() -> dict[str, Any]:
    python_ok = importlib.util.find_spec("pptx") is not None
    node_ok, node_detail = _node_can_resolve("pptxgenjs")
    checks = {
        "node": {"available": shutil.which("node") is not None},
        "pptxgenjs": {"available": node_ok, "detail": node_detail},
        "python_pptx": {"available": python_ok},
        "soffice": {"available": shutil.which("soffice") is not None},
        "pdftoppm": {"available": shutil.which("pdftoppm") is not None},
    }
    missing = []
    if not checks["node"]["available"]:
        missing.append("Node.js")
    if not node_ok:
        missing.append("pptxgenjs")
    if not python_ok:
        missing.append("python-pptx")
    return {
        "backend": "integrated-presentation-skill",
        "status": "available" if not missing else "blocked",
        "root": str(ROOT),
        "skill_file": str(ROOT / "SKILL.md"),
        "renderer": str(RENDERER),
        "qa": str(QA),
        "checks": checks,
        "missing": missing,
        "message": "ready" if not missing else "Missing runtime: " + ", ".join(missing),
    }


def _run(command: list[str]) -> int:
    result = subprocess.run(command)
    return result.returncode


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    _add_common(check)
    build = subparsers.add_parser("build")
    build.add_argument("--outline", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--style-preset", default="executive-clinical")
    build.add_argument("--asset-root")
    qa = subparsers.add_parser("qa")
    qa.add_argument("--input", required=True)
    qa.add_argument("--outdir", required=True)
    qa.add_argument("--outline")
    qa.add_argument("--skip-render", action="store_true")
    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("--input", required=True)
    inventory.add_argument("--output", required=True)
    extract = subparsers.add_parser("extract")
    extract.add_argument("--input", required=True)
    extract.add_argument("--output")
    args = parser.parse_args(argv)

    report = capability_report()
    if args.command == "check":
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else report["message"])
        return 0 if report["status"] == "available" else 2
    if report["status"] != "available":
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    if args.command == "build":
        command = ["node", str(RENDERER), "--outline", args.outline, "--output", args.output, "--style-preset", args.style_preset]
        if args.asset_root:
            command.extend(["--asset-root", args.asset_root])
        return _run(command)
    if args.command == "qa":
        command = [sys.executable, str(QA), "--input", args.input, "--outdir", args.outdir]
        if args.outline:
            command.extend(["--outline", args.outline])
        if args.skip_render:
            command.append("--skip-render")
        return _run(command)
    if args.command == "inventory":
        return _run([sys.executable, str(INVENTORY), "--input", args.input, "--output", args.output])
    command = [sys.executable, str(EXTRACT), "--input", args.input]
    if args.output:
        command.extend(["--output", args.output])
    return _run(command)


if __name__ == "__main__":
    raise SystemExit(main())

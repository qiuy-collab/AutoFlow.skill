#!/usr/bin/env python3
"""Offline AutoFlow adapter for the curated presentation-skill surface."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
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
RENDER_CACHE = ".autoflow-render-cache.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _render_cache_key(input_path: Path) -> dict[str, str]:
    return {
        "input_sha256": _sha256(input_path),
        "adapter_sha256": _sha256(Path(__file__).resolve()),
    }


def _render_cache_valid(input_path: Path, render_dir: Path) -> bool:
    metadata = render_dir / RENDER_CACHE
    if not metadata.is_file():
        return False
    try:
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        from pptx import Presentation

        expected = len(Presentation(str(input_path)).slides)
    except (OSError, json.JSONDecodeError, ImportError):
        return False
    rendered = list(render_dir.glob("slide-*.png"))
    return (
        payload.get("input_key") == _render_cache_key(input_path)
        and payload.get("slide_count") == expected
        and len(rendered) == expected
        and all(path.stat().st_size > 0 for path in rendered)
    )


def _write_render_cache(input_path: Path, render_dir: Path, slide_count: int) -> None:
    payload = {"input_key": _render_cache_key(input_path), "slide_count": slide_count}
    (render_dir / RENDER_CACHE).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
        "windows_powerpoint": {
            "available": os.name == "nt" and shutil.which("powershell") is not None,
            "detail": "Used as the local render fallback when soffice is unavailable.",
        },
    }
    renderer_missing = []
    if not checks["node"]["available"]:
        renderer_missing.append("Node.js")
    if not node_ok:
        renderer_missing.append("pptxgenjs")
    qa_missing = []
    if not python_ok:
        qa_missing.append("python-pptx")
    missing = renderer_missing + qa_missing
    return {
        "backend": "integrated-presentation-skill",
        "status": "available" if not missing else "blocked",
        "renderer_status": "available" if not renderer_missing else "blocked",
        "qa_status": "available" if not qa_missing else "blocked",
        "root": str(ROOT),
        "skill_file": str(ROOT / "SKILL.md"),
        "renderer": str(RENDERER),
        "qa": str(QA),
        "checks": checks,
        "missing": missing,
        "message": "ready" if not missing else "Missing runtime: " + ", ".join(missing),
    }


def _command_missing(report: dict[str, Any], command: str) -> list[str]:
    requirements = {
        "build": ("node", "pptxgenjs"),
        "qa": ("python_pptx",),
        "inventory": ("python_pptx",),
        "extract": ("python_pptx",),
    }
    missing = []
    for key in requirements.get(command, ()):
        if not report.get("checks", {}).get(key, {}).get("available", False):
            missing.append("Node.js" if key == "node" else key.replace("_", "-"))
    return missing


def _run(command: list[str]) -> int:
    result = subprocess.run(command)
    return result.returncode


def _render_with_windows_powerpoint(input_path: Path, render_dir: Path) -> tuple[int, str]:
    """Render a PPTX with installed PowerPoint without requiring pywin32."""
    powershell = shutil.which("powershell")
    if os.name != "nt" or not powershell:
        return 2, "Windows PowerPoint fallback is unavailable"
    render_dir.mkdir(parents=True, exist_ok=True)
    for stale in render_dir.glob("slide-*.png"):
        stale.unlink()
    env = os.environ.copy()
    env["AUTOFLOW_PPT_INPUT"] = str(input_path.resolve())
    env["AUTOFLOW_PPT_OUTDIR"] = str(render_dir.resolve())
    script = (
        "$ErrorActionPreference='Stop';"
        "$pp=New-Object -ComObject PowerPoint.Application;"
        "try {"
        "$pres=$pp.Presentations.Open($env:AUTOFLOW_PPT_INPUT,$true,$false,$false);"
        "$pres.SaveAs($env:AUTOFLOW_PPT_OUTDIR,18);"
        "$count=$pres.Slides.Count;"
        "$pres.Close();"
        "Write-Output ('slides='+$count)"
        "} finally { try {$pp.Quit()} catch {} }"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        return result.returncode, (result.stdout + "\n" + result.stderr).strip()
    exported = sorted(
        [path for path in render_dir.iterdir() if path.suffix.lower() == ".png"],
        key=lambda path: int(re.search(r"(\d+)", path.stem).group(1)) if re.search(r"(\d+)", path.stem) else 10**9,
    )
    for index, path in enumerate(exported, start=1):
        target = render_dir / f"slide-{index}.png"
        if path != target:
            path.replace(target)
    _write_render_cache(input_path, render_dir, len(exported))
    return 0, result.stdout.strip()


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
    qa.add_argument("--force-render", action="store_true", help="Ignore a valid render cache.")
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
    command_missing = _command_missing(report, args.command)
    if command_missing:
        blocked = {**report, "command": args.command, "missing": command_missing}
        print(json.dumps(blocked, ensure_ascii=False, indent=2), file=sys.stderr)
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
        use_powerpoint_fallback = (
            not args.skip_render
            and not report["checks"]["soffice"]["available"]
            and report["checks"]["windows_powerpoint"]["available"]
        )
        if use_powerpoint_fallback:
            input_path = Path(args.input).expanduser().resolve()
            render_dir = Path(args.outdir).expanduser().resolve() / "renders"
            if not args.force_render and _render_cache_valid(input_path, render_dir):
                print("PowerPoint render cache: reused unchanged slide images")
            else:
                render_rc, render_detail = _render_with_windows_powerpoint(input_path, render_dir)
                if render_rc:
                    print(f"PowerPoint render fallback failed: {render_detail}", file=sys.stderr)
                    return render_rc
                print(f"PowerPoint render fallback: {render_detail}")
            command.append("--skip-render")
        elif args.skip_render:
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

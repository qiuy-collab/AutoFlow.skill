#!/usr/bin/env python3
"""Run AutoFlow's integrated minimax-docx OpenXML core without external Skill lookup."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


CORE_SCHEMA = "autoflow/word-core-validation/1.0"


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def project_path() -> Path:
    return skill_root() / "integrations" / "minimax-docx" / "scripts" / "dotnet" / "MiniMaxAIDocx.Cli" / "MiniMaxAIDocx.Cli.csproj"


def bundled_executable() -> Path:
    return skill_root() / "integrations" / "minimax-docx" / "scripts" / "dotnet" / "MiniMaxAIDocx.Cli" / "bin" / "Debug" / "net8.0" / "MiniMaxAIDocx.Cli.exe"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capability() -> dict:
    project = project_path()
    dotnet = shutil.which("dotnet")
    executable = bundled_executable()
    return {
        "backend": "integrated-minimax-docx-core",
        "integration_root": str(project.parent.parent.parent.parent.resolve()),
        "status": "available" if project.is_file() and dotnet else "blocked",
        "project": str(project),
        "project_present": project.is_file(),
        "dotnet": dotnet or "",
        "bundled_executable": str(executable),
        "bundled_executable_present": executable.is_file(),
        "external_skill_required": False,
    }


def run_core(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    cap = capability()
    if cap["status"] != "available":
        raise SystemExit(
            "Integrated Word core is present but cannot execute because the .NET 8 runtime/SDK "
            "is unavailable. Install dotnet; no external Skill fallback was invoked."
        )
    if bundled_executable().is_file():
        command = [str(bundled_executable()), *arguments]
    else:
        command = [cap["dotnet"], "run", "--project", str(project_path()), "--", *arguments]
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")


def parse_json_output(result: subprocess.CompletedProcess[str], step: str) -> dict:
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        raise SystemExit(f"Integrated Word core {step} failed.\n{details}".rstrip())
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Integrated Word core {step} returned invalid JSON: {result.stdout}") from exc


def validate_document(args: argparse.Namespace) -> int:
    document = args.document.expanduser().resolve()
    if not document.is_file() or document.suffix.lower() != ".docx":
        raise SystemExit(f"Word document not found or not .docx: {document}")
    template = args.template.expanduser().resolve() if args.template else None
    if template and (not template.is_file() or template.suffix.lower() != ".docx"):
        raise SystemExit(f"Template not found or not .docx: {template}")
    source = args.source.expanduser().resolve() if args.source else None
    if source and (not source.is_file() or source.suffix.lower() != ".docx"):
        raise SystemExit(f"Source not found or not .docx: {source}")

    xsd = skill_root() / "integrations" / "minimax-docx" / "assets" / "xsd" / "wml-subset.xsd"
    validation_args = ["validate", "--input", str(document), "--xsd", str(xsd), "--business", "--json"]
    if template:
        validation_args.extend(["--gate-check", str(template)])
    validation = parse_json_output(run_core(validation_args), "validation")

    dry_merge = run_core(["merge-runs", "--input", str(document), "--dry-run"])
    if dry_merge.returncode != 0:
        raise SystemExit(f"Integrated Word core merge-runs preflight failed.\n{dry_merge.stderr}")

    diff = None
    baseline = source or template
    if baseline:
        diff = parse_json_output(
            run_core(["diff", "--before", str(baseline), "--after", str(document), "--json"]),
            "diff",
        )

    report = {
        "$schema": CORE_SCHEMA,
        "backend": capability(),
        "document": {"path": str(document), "sha256": sha256(document)},
        "template": str(template) if template else None,
        "source": str(source) if source else None,
        "checks": {
            "xsd_and_business": validation,
            "merge_runs_dry_run": dry_merge.stdout.strip(),
            "diff": diff,
        },
        "overall_pass": validation.get("isValid") is True,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.report)
    return 0 if report["overall_pass"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Report whether the integrated backend can really execute.")
    check.add_argument("--json", action="store_true")
    invoke = sub.add_parser("invoke", help="Pass arguments directly to the integrated minimax-docx CLI.")
    invoke.add_argument("arguments", nargs=argparse.REMAINDER)
    validate = sub.add_parser("validate", help="Run XSD, business, template gate, and diff checks.")
    validate.add_argument("--document", type=Path, required=True)
    validate.add_argument("--template", type=Path)
    validate.add_argument("--source", type=Path)
    validate.add_argument("--report", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "check":
        data = capability()
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"{data['status']}: {data['backend']}")
            print(f"project: {data['project']}")
            print(f"dotnet: {data['dotnet'] or 'missing'}")
        return 0 if data["status"] == "available" else 1
    if args.command == "invoke":
        forwarded = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        result = run_core(forwarded)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode
    if args.command == "validate":
        return validate_document(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

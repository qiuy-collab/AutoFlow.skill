#!/usr/bin/env python3
"""AutoFlow office backend engine driven by the officecli binary (no external Skill lookup)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ENGINE_SCHEMA = "autoflow/office-engine-validation/1.0"
OFFICE_FORMATS = {"word", "ppt", "excel"}
FORMAT_SUFFIX = {"word": ".docx", "ppt": ".pptx", "excel": ".xlsx"}


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_officecli() -> str:
    """Locate the officecli binary: PATH first, then common install locations."""
    found = shutil.which("officecli")
    if found:
        return found
    home = Path.home()
    candidates = [
        home / ".officecli" / "bin" / "officecli",
        home / ".officecli" / "bin" / "officecli.exe",
        home / ".local" / "bin" / "officecli",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "officecli" / "officecli.exe",
        Path("C:/Program Files/officecli/officecli.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    return ""


def officecli_version(exe: str) -> str:
    try:
        result = subprocess.run([exe, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        output = (result.stdout or result.stderr).strip()
        return output.splitlines()[0] if output else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def capability() -> dict:
    exe = find_officecli()
    if not exe:
        return {
            "backend": "officecli",
            "integration_root": str(skill_root()),
            "status": "missing",
            "exe": "",
            "version": "",
            "external_skill_required": False,
            "message": "officecli is not installed. Install it (https://d.officecli.ai/install.sh) or add it to PATH; "
            "AutoFlow will not silently substitute another backend.",
        }
    version = officecli_version(exe)
    return {
        "backend": "officecli",
        "integration_root": str(skill_root()),
        "status": "available" if version else "blocked",
        "exe": exe,
        "version": version,
        "external_skill_required": False,
        **({} if version else {"message": "officecli found but --version did not respond; check the binary."}),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validator_fingerprint() -> str:
    digest = hashlib.sha256()
    tracked = [Path(__file__).resolve(), skill_root() / "scripts" / "validate_office.py"]
    for path in tracked:
        if not path.is_file():
            continue
        digest.update(str(path.relative_to(skill_root())).encode("utf-8"))
        digest.update(sha256(path).encode("ascii"))
    return digest.hexdigest()


def validation_cache_key(document: Path, template: Path | None, source: Path | None) -> dict:
    def item(path: Path | None) -> dict | None:
        return {"path": str(path), "sha256": sha256(path)} if path else None

    return {
        "document": item(document),
        "template": item(template),
        "source": item(source),
        "validator_fingerprint": validator_fingerprint(),
    }


def reusable_report(path: Path, cache_key: dict) -> dict | None:
    if not path.is_file():
        return None
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        report.get("$schema") == ENGINE_SCHEMA
        and report.get("overall_pass") is True
        and (report.get("cache") or {}).get("input_key") == cache_key
    ):
        return report
    return None


def run_officecli(exe: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [exe, *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )


def _cli_json(result: subprocess.CompletedProcess[str], step: str) -> dict:
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        return {"ok": False, "error": f"officecli {step} returned invalid JSON: {details[:2000]}"}
    return {"ok": result.returncode == 0, "payload": payload}


def engine_checks(exe: str, document: Path, format_name: str) -> list[dict]:
    """Run officecli validate (OpenXML schema) and view issues (content/structure) checks."""
    checks: list[dict] = []

    schema_result = run_officecli(exe, ["validate", str(document), "--json"])
    schema = _cli_json(schema_result, "validate")
    payload = schema.get("payload") or {}
    data_text = payload.get("data") if isinstance(payload.get("data"), str) else ""
    schema_passed = (
        schema["ok"]
        and payload.get("success") is True
        and "no errors" in str(data_text).casefold()
    )
    if schema_passed:
        checks.append({"name": "openxml_schema", "status": "passed", "evidence": "officecli validate passed"})
    else:
        detail = payload or {"error": schema.get("error", "unknown failure")}
        checks.append(
            {
                "name": "openxml_schema",
                "status": "failed",
                "evidence": f"officecli validate failed: {json.dumps(detail, ensure_ascii=False)[:2000]}",
            }
        )

    issues_result = run_officecli(exe, ["view", str(document), "issues", "--json"])
    issues = _cli_json(issues_result, "view issues")
    payload = issues.get("payload") or {}
    if issues["ok"] and payload.get("success") is True:
        data_node = payload.get("data") or {}
        raw = data_node.get("issues") if isinstance(data_node, dict) else data_node
        if not isinstance(raw, list):
            raw = []
        formatted = [item.get("message", str(item)) if isinstance(item, dict) else str(item) for item in raw]
        filtered = [item for item in formatted if item.strip()]
        checks.append(
            {
                "name": "officecli_issues",
                "status": "passed" if not filtered else "failed",
                "evidence": "officecli view issues found no problems" if not filtered else "issues: " + "; ".join(filtered[:20]),
            }
        )
    else:
        checks.append(
            {
                "name": "officecli_issues",
                "status": "failed",
                "evidence": f"officecli view issues failed: {issues.get('error', 'unknown')[:2000]}",
            }
        )
    return checks


def validate_document(args: argparse.Namespace) -> int:
    cap = capability()
    if cap["status"] != "available":
        raise SystemExit(cap.get("message", "officecli backend is unavailable."))
    exe = cap["exe"]

    document = args.document.expanduser().resolve()
    expected_suffix = FORMAT_SUFFIX[args.format]
    if not document.is_file() or document.suffix.lower() != expected_suffix:
        raise SystemExit(f"Office document not found or not {expected_suffix}: {document}")
    template = args.template.expanduser().resolve() if args.template else None
    if template and (not template.is_file() or template.suffix.lower() != expected_suffix):
        raise SystemExit(f"Template not found or not {expected_suffix}: {template}")
    source = args.source.expanduser().resolve() if args.source else None
    if source and (not source.is_file() or source.suffix.lower() != expected_suffix):
        raise SystemExit(f"Source not found or not {expected_suffix}: {source}")

    cache_key = validation_cache_key(document, template, source)
    if not args.force:
        cached = reusable_report(args.report, cache_key)
        if cached is not None:
            cached.setdefault("cache", {})["hit"] = True
            args.report.write_text(json.dumps(cached, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(args.report)
            return 0

    checks = engine_checks(exe, document, args.format)
    engine_report = {
        "$schema": ENGINE_SCHEMA,
        "engine": {"name": "officecli", "exe": exe, "version": cap["version"]},
        "format": args.format,
        "document": {"path": str(document), "sha256": sha256(document)},
        "template": str(template) if template else None,
        "source": str(source) if source else None,
        "checks": checks,
        "overall_pass": all(item["status"] == "passed" for item in checks),
        "cache": {"input_key": cache_key, "hit": False},
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(engine_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.report)
    return 0 if engine_report["overall_pass"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Report whether the officecli backend can really execute.")
    check.add_argument("--json", action="store_true")
    validate = sub.add_parser("validate", help="Run officecli schema/issues checks and produce an engine report.")
    validate.add_argument("--document", type=Path, required=True)
    validate.add_argument("--format", required=True, choices=sorted(OFFICE_FORMATS))
    validate.add_argument("--template", type=Path)
    validate.add_argument("--source", type=Path)
    validate.add_argument("--report", type=Path, required=True)
    validate.add_argument("--force", action="store_true", help="Ignore a matching passed validation report.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "check":
        data = capability()
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"{data['status']}: {data['backend']} ({data.get('exe', '') or 'not found'})")
        return 0 if data["status"] == "available" else 1
    if args.command == "validate":
        return validate_document(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

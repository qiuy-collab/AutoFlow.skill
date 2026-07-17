import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


FORBIDDEN_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "sent_mails",
}
FORBIDDEN_NAMES = {
    ".env",
    ".env.local",
    "id_rsa",
    "id_ed25519",
    "db.sqlite3",
    "baseline.sqlite3",
    "production-check.sqlite3",
}
FORBIDDEN_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".pyc", ".pyo")


def parse_args():
    parser = argparse.ArgumentParser(description="Assemble and verify declared AutoFlow delivery artifacts.")
    parser.add_argument("--config", required=True, help="Path to the package module plan JSON")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--validate-plan",
        action="store_true",
        help="Validate package paths and requirement mappings without requiring future source artifacts.",
    )
    mode.add_argument(
        "--verify-only",
        action="store_true",
        help="Read-only verification of the published folder, archive, and manifest.",
    )
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return (root / path).resolve() if not path.is_absolute() else path.resolve()


def normalized_rel(value: str | Path) -> str:
    return str(PurePosixPath(str(value).replace("\\", "/")))


def glob_matches(rel_path: str, patterns: list[str]) -> bool:
    normalized = normalized_rel(rel_path)
    return any(fnmatch.fnmatchcase(normalized, pattern.replace("\\", "/")) for pattern in patterns)


def forbidden_reason(rel_path: str) -> str:
    path = PurePosixPath(normalized_rel(rel_path))
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if parts & FORBIDDEN_DIRS:
        return "forbidden_directory"
    if name in FORBIDDEN_NAMES or name.startswith("~$"):
        return "sensitive_or_runtime_file"
    if name.endswith(FORBIDDEN_SUFFIXES):
        return "sensitive_or_cache_suffix"
    return ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_explicit_source_is_safe(source: Path, source_root: Path) -> None:
    try:
        rel = normalized_rel(source.relative_to(source_root))
    except ValueError:
        rel = normalized_rel(source)
    reason = forbidden_reason(rel)
    if reason:
        raise SystemExit(f"Refusing explicitly included sensitive/runtime path: {source} ({reason})")
    if source.is_symlink():
        raise SystemExit(f"Refusing explicitly included symbolic link: {source}")


def collect_files(config_path: Path, config: dict):
    source_root = normalize_path(config_path.parent, config["source_root"])
    include_paths = config.get("include_paths", [])
    exclude_globs = list(config.get("exclude_globs", []))
    flatten = bool(config.get("flatten", False))
    selected: list[tuple[Path, str, list[str], str]] = []
    seen_archives: set[str] = set()
    exclusions: Counter[str] = Counter()

    for item in include_paths:
        source = normalize_path(source_root, item["path"])
        archive_root = normalized_rel(item.get("archive_root", ""))
        requirement_ids = item.get("requirement_ids", [])
        if not isinstance(requirement_ids, list) or not requirement_ids:
            raise SystemExit(f"Package include path must map to requirement_ids: {source}")
        if not source.exists():
            raise SystemExit(f"Submission include path does not exist: {source}")
        _ensure_explicit_source_is_safe(source, source_root)

        candidates = [source] if source.is_file() else sorted(path for path in source.rglob("*") if path.is_file())
        for file_path in candidates:
            if file_path.is_symlink():
                exclusions["symbolic_link"] += 1
                continue
            source_rel = normalized_rel(file_path.relative_to(source_root))
            rel_tail = file_path.name if source.is_file() else normalized_rel(file_path.relative_to(source))
            archive_name = file_path.name if flatten else normalized_rel(PurePosixPath(archive_root) / rel_tail)
            if glob_matches(source_rel, exclude_globs) or glob_matches(archive_name, exclude_globs):
                exclusions["configured_glob"] += 1
                continue
            reason = forbidden_reason(source_rel) or forbidden_reason(archive_name)
            if reason:
                exclusions[reason] += 1
                continue
            if archive_name in seen_archives:
                raise SystemExit(f"Duplicate archive path from include_paths: {archive_name}")
            seen_archives.add(archive_name)
            selected.append((file_path, archive_name, requirement_ids, sha256(file_path)))

    return source_root, selected, dict(sorted(exclusions.items()))


def validate_package_plan(config_path: Path, config: dict) -> dict:
    include_paths = config.get("include_paths")
    if not isinstance(include_paths, list) or not include_paths:
        raise SystemExit("Package plan must declare at least one include_paths item")
    for index, item in enumerate(include_paths, start=1):
        if not isinstance(item, dict) or not str(item.get("path", "")).strip():
            raise SystemExit(f"Package include item {index} must declare a path")
        requirement_ids = item.get("requirement_ids")
        if not isinstance(requirement_ids, list) or not any(str(value).strip() for value in requirement_ids):
            raise SystemExit(f"Package include item {index} must map to requirement_ids")

    allowed_output_root = normalize_path(config_path.parent, config.get("allowed_output_root", "."))
    output_zip = normalize_path(config_path.parent, config.get("output_zip", "submit.zip"))
    output_folder = normalize_path(config_path.parent, config.get("output_folder", str(output_zip.parent / "submit")))
    for label, target in (("output_zip", output_zip), ("output_folder", output_folder)):
        if target == allowed_output_root or allowed_output_root not in target.parents:
            raise SystemExit(f"{label} must stay below allowed_output_root: {allowed_output_root}")
    if output_zip == output_folder or output_zip in output_folder.parents or output_folder in output_zip.parents:
        raise SystemExit("output_zip and output_folder must be distinct non-nested paths")
    return {
        "status": "valid",
        "include_items": len(include_paths),
        "output_zip": str(output_zip),
        "output_folder": str(output_folder),
    }


def package_paths(config_path: Path, config: dict) -> tuple[Path, Path, Path]:
    output_zip = normalize_path(config_path.parent, config.get("output_zip", "submit.zip"))
    output_folder = normalize_path(config_path.parent, config.get("output_folder", str(output_zip.parent / "submit")))
    manifest_path = output_zip.with_name(output_zip.stem + "_manifest.json")
    return output_folder, output_zip, manifest_path


def _folder_records(folder: Path) -> list[dict]:
    return [
        {
            "archive_path": normalized_rel(path.relative_to(folder)),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(item for item in folder.rglob("*") if item.is_file())
    ]


def verify_package(config_path: Path, config: dict) -> dict:
    validate_package_plan(config_path, config)
    output_folder, output_zip, manifest_path = package_paths(config_path, config)
    for path in (output_folder, output_zip, manifest_path):
        if not path.exists():
            raise SystemExit(f"Published package component is missing: {path}")
    manifest = load_json(manifest_path)
    folder_records = _folder_records(output_folder)
    folder_names = [item["archive_path"] for item in folder_records]
    manifest_records = sorted([
        {"archive_path": item["archive_path"], "size": item["size"], "sha256": item["sha256"]}
        for item in manifest.get("files", [])
    ], key=lambda item: item["archive_path"])
    with zipfile.ZipFile(output_zip) as archive:
        archive_names = sorted(archive.namelist())
        bad_member = archive.testzip()
    forbidden = [name for name in archive_names if forbidden_reason(name)]
    checks = {
        "manifest_overall_pass": bool(manifest.get("overall_pass")),
        "folder_manifest_match": folder_records == manifest_records,
        "folder_archive_match": folder_names == archive_names,
        "zip_integrity": bad_member is None,
        "no_sensitive_files": not forbidden,
    }
    result = {
        "$schema": "autoflow/package-verification/1.0",
        "mode": "read_only",
        "output_folder": str(output_folder),
        "output_zip": str(output_zip),
        "manifest": str(manifest_path),
        "file_count": len(folder_names),
        "checks": checks,
        "overall_pass": all(checks.values()),
    }
    if not result["overall_pass"]:
        raise SystemExit("Published package read-only verification failed:\n" + json.dumps(result, ensure_ascii=False, indent=2))
    return result


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _publish_outputs(pairs: list[tuple[Path, Path]]) -> None:
    """Publish all staged outputs as one rollback-capable transaction."""
    backups: list[tuple[Path, Path]] = []
    published: list[Path] = []
    try:
        for _, target in pairs:
            backup = target.with_name(target.name + ".previous")
            _remove_path(backup)
            if target.exists() or target.is_symlink():
                target.replace(backup)
                backups.append((target, backup))
        for staged, target in pairs:
            staged.replace(target)
            published.append(target)
    except Exception:
        for target in reversed(published):
            _remove_path(target)
        for target, backup in reversed(backups):
            if backup.exists() or backup.is_symlink():
                backup.replace(target)
        raise
    else:
        for _, backup in backups:
            _remove_path(backup)


def package_submission(config_path: Path):
    config = load_json(config_path)
    validate_package_plan(config_path, config)
    if not config.get("enabled", False):
        raise SystemExit("package plan is not enabled")
    output_folder, output_zip, manifest_path = package_paths(config_path, config)
    output_folder.parent.mkdir(parents=True, exist_ok=True)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    source_root, files, exclusions = collect_files(config_path, config)
    if not files:
        raise SystemExit("package plan did not resolve any files to package")

    staging = Path(tempfile.mkdtemp(prefix=f".{output_folder.name}.staging-", dir=output_folder.parent))
    temp_zip = output_zip.with_name(output_zip.name + ".tmp")
    temp_manifest = manifest_path.with_name(manifest_path.name + ".tmp")
    try:
        for source, archive_name, _, _ in files:
            destination = staging / Path(archive_name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in sorted(item for item in staging.rglob("*") if item.is_file()):
                archive.write(file_path, normalized_rel(file_path.relative_to(staging)))

        folder_names = sorted(normalized_rel(path.relative_to(staging)) for path in staging.rglob("*") if path.is_file())
        with zipfile.ZipFile(temp_zip) as archive:
            archive_names = sorted(archive.namelist())
            bad_member = archive.testzip()
        checks = [
            {"name": "folder_archive_match", "status": "passed" if folder_names == archive_names else "failed"},
            {"name": "zip_integrity", "status": "passed" if bad_member is None else "failed"},
            {"name": "no_sensitive_files", "status": "passed" if not any(forbidden_reason(name) for name in archive_names) else "failed"},
            {"name": "requirement_mapping", "status": "passed" if all(ids for _, _, ids, _ in files) else "failed"},
        ]
        manifest = {
            "$schema": "autoflow/package-manifest/1.0",
            "source_root": str(source_root),
            "output_zip": str(output_zip),
            "output_folder": str(output_folder),
            "file_count": len(files),
            "excluded": {"count": sum(exclusions.values()), "by_reason": exclusions},
            "files": sorted([
                {
                    "source": str(source),
                    "archive_path": archive_name,
                    "size": source.stat().st_size,
                    "sha256": digest,
                    "requirement_ids": requirement_ids,
                }
                for source, archive_name, requirement_ids, digest in files
            ], key=lambda item: item["archive_path"]),
            "checks": checks,
            "overall_pass": all(item["status"] == "passed" for item in checks),
        }
        if not manifest["overall_pass"]:
            raise SystemExit("Package staging validation failed")
        temp_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _publish_outputs([
            (staging, output_folder),
            (temp_zip, output_zip),
            (temp_manifest, manifest_path),
        ])
        result = verify_package(config_path, config)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        for temp in (temp_zip, temp_manifest):
            if temp.exists():
                temp.unlink()

    print(f"Submission folder written: {output_folder}")
    print(f"Submission archive written: {output_zip}")
    print(f"Submission manifest written: {manifest_path}")
    print(json.dumps(result, ensure_ascii=False))


def main():
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    config = load_json(config_path)
    if args.validate_plan:
        print(json.dumps(validate_package_plan(config_path, config), ensure_ascii=False, indent=2))
        return
    if args.verify_only:
        print(json.dumps(verify_package(config_path, config), ensure_ascii=False, indent=2))
        return
    package_submission(config_path)


if __name__ == "__main__":
    main()

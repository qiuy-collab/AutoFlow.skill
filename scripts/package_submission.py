import argparse
import hashlib
import json
import os
import zipfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Assemble declared AutoFlow artifacts into a delivery folder and archive.")
    parser.add_argument("--config", required=True, help="Path to the package module plan JSON")
    parser.add_argument(
        "--validate-plan",
        action="store_true",
        help="Validate package paths and requirement mappings without requiring future source artifacts.",
    )
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (root / path).resolve()
    else:
        path = path.resolve()
    return path


def should_exclude(rel_path: str, exclude_globs: list[str]) -> bool:
    normalized = rel_path.replace("\\", "/")
    return any(Path(normalized).match(pattern) for pattern in exclude_globs)


def is_sensitive(rel_path: str) -> bool:
    path = Path(rel_path.replace("\\", "/"))
    name = path.name.lower()
    return (
        name in {".env", ".env.local", "id_rsa", "id_ed25519"}
        or name.endswith((".pem", ".key", ".p12", ".pfx"))
        or "__pycache__" in path.parts
        or ".git" in path.parts
        or name.startswith("~$")
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(config_path: Path, config: dict):
    source_root = normalize_path(config_path.parent, config["source_root"])
    include_paths = config.get("include_paths", [])
    exclude_globs = config.get("exclude_globs", [])
    flatten = bool(config.get("flatten", False))

    selected = []
    seen_archives = set()

    for item in include_paths:
        source = normalize_path(source_root, item["path"])
        archive_root = item.get("archive_root", "")
        requirement_ids = item.get("requirement_ids", [])
        if not isinstance(requirement_ids, list) or not requirement_ids:
            raise SystemExit(f"Package include path must map to requirement_ids: {source}")
        if not source.exists():
            raise SystemExit(f"Submission include path does not exist: {source}")

        if source.is_file():
            rel_name = source.name if flatten else str(Path(archive_root) / source.name)
            rel_name = rel_name.replace("\\", "/")
            if should_exclude(rel_name, exclude_globs):
                continue
            if is_sensitive(rel_name):
                raise SystemExit(f"Refusing to package sensitive or temporary file: {rel_name}")
            if rel_name not in seen_archives:
                seen_archives.add(rel_name)
                selected.append((source, rel_name, requirement_ids))
            continue

        for file_path in sorted(path for path in source.rglob("*") if path.is_file()):
            rel_tail = file_path.relative_to(source)
            rel_name = str(Path(archive_root) / rel_tail) if not flatten else file_path.name
            rel_name = rel_name.replace("\\", "/")
            if should_exclude(rel_name, exclude_globs):
                continue
            if is_sensitive(rel_name):
                raise SystemExit(f"Refusing to package sensitive or temporary file: {rel_name}")
            if rel_name not in seen_archives:
                seen_archives.add(rel_name)
                selected.append((file_path, rel_name, requirement_ids))

    return source_root, selected


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


def package_submission(config_path: Path):
    config = load_json(config_path)
    validate_package_plan(config_path, config)
    if not config.get("enabled", False):
        raise SystemExit("submission_package.json is not enabled")

    allowed_output_root = normalize_path(config_path.parent, config.get("allowed_output_root", "."))
    output_zip = normalize_path(config_path.parent, config.get("output_zip", "submit.zip"))
    output_folder = normalize_path(config_path.parent, config.get("output_folder", str(output_zip.parent / "submit")))
    for label, target in (("output_zip", output_zip), ("output_folder", output_folder)):
        if target == allowed_output_root or allowed_output_root not in target.parents:
            raise SystemExit(f"{label} must stay below allowed_output_root: {allowed_output_root}")
    source_root, files = collect_files(config_path, config)
    if not files:
        raise SystemExit("submission_package.json did not resolve any files to package")

    # Create submit/ folder
    if output_folder.exists():
        import shutil
        shutil.rmtree(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    for source, rel_name, _ in files:
        dest = output_folder / rel_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(str(source), str(dest))

    # Create submit.zip from submit/ folder
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(output_folder.rglob("*")):
            if file_path.is_file():
                arcname = str(file_path.relative_to(output_folder))
                zf.write(file_path, arcname)

    with zipfile.ZipFile(output_zip) as archive:
        archive_names = sorted(archive.namelist())
    folder_names = sorted(str(path.relative_to(output_folder)).replace("\\", "/") for path in output_folder.rglob("*") if path.is_file())
    checks = [
        {
            "name": "folder_archive_match",
            "status": "passed" if archive_names == folder_names else "failed",
            "evidence": f"folder_files={len(folder_names)}, archive_files={len(archive_names)}",
        },
        {
            "name": "no_sensitive_files",
            "status": "passed" if not any(is_sensitive(name) for name in archive_names) else "failed",
            "evidence": "Archive listing scanned for secrets, VCS data, caches, and Office temp files",
        },
        {
            "name": "requirement_mapping",
            "status": "passed" if all(requirement_ids for _, _, requirement_ids in files) else "failed",
            "evidence": "Every included path maps to at least one requirement id",
        },
    ]
    manifest = {
        "$schema": "autoflow/package-manifest/1.0",
        "source_root": str(source_root),
        "output_zip": str(output_zip),
        "output_folder": str(output_folder),
        "file_count": len(files),
        "files": [
            {
                "source": str(source),
                "archive_path": rel_name,
                "size": os.path.getsize(source),
                "sha256": sha256(source),
                "requirement_ids": requirement_ids,
            }
            for source, rel_name, requirement_ids in files
        ],
        "checks": checks,
        "overall_pass": all(item["status"] == "passed" for item in checks),
    }
    manifest_path = output_zip.with_name(output_zip.stem + "_manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if not manifest["overall_pass"]:
        raise SystemExit(f"Submission package validation failed; inspect {manifest_path}")
    print(f"Submission folder written: {output_folder}")
    print(f"Submission archive written: {output_zip}")
    print(f"Submission manifest written: {manifest_path}")


def main():
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    if args.validate_plan:
        result = validate_package_plan(config_path, load_json(config_path))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    package_submission(config_path)


if __name__ == "__main__":
    main()

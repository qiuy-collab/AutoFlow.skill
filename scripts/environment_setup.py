import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "autoflow/environment-report/1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_args():
    parser = argparse.ArgumentParser(description="Detect, provision, and verify a project environment outside source artifacts.")
    parser.add_argument("command", choices=["detect", "ensure", "verify"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    return parser.parse_args()


def run(command: list[str], *, cwd: Path | None, timeout: int, actions: list[dict], env: dict | None = None) -> subprocess.CompletedProcess:
    started = utc_now()
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        record = {
            "command": command,
            "cwd": str(cwd) if cwd else "",
            "started_at": started,
            "completed_at": utc_now(),
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        result = subprocess.CompletedProcess(command, 127, "", str(exc))
        record = {
            "command": command,
            "cwd": str(cwd) if cwd else "",
            "started_at": started,
            "completed_at": utc_now(),
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }
    actions.append(record)
    return result


def project_kinds(project: Path) -> list[str]:
    kinds = []
    if any((project / name).exists() for name in ("requirements.txt", "pyproject.toml", "setup.py", "manage.py")):
        kinds.append("python")
    if (project / "package.json").is_file():
        kinds.append("node")
    if (project / "pom.xml").is_file() or any(project.glob("build.gradle*")) or (project / "gradlew").exists():
        kinds.append("java")
    if (project / "composer.json").is_file():
        kinds.append("php")
    if any(project.glob("*.sln")) or any(project.rglob("*.csproj")):
        kinds.append("dotnet")
    return kinds


def executable(name: str) -> str:
    return shutil.which(name) or ""


def refresh_windows_path() -> None:
    if os.name != "nt":
        return
    try:
        import winreg

        values = []
        for hive, key_name in (
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            (winreg.HKEY_CURRENT_USER, r"Environment"),
        ):
            with winreg.OpenKey(hive, key_name) as key:
                value, _ = winreg.QueryValueEx(key, "Path")
                values.append(os.path.expandvars(value))
        values.append(os.environ.get("PATH", ""))
        os.environ["PATH"] = os.pathsep.join(value for value in values if value)
    except (OSError, ImportError):
        pass


def dependency_fingerprint(project: Path) -> str:
    names = {
        "requirements.txt", "pyproject.toml", "setup.py", "package.json",
        "package-lock.json", "npm-shrinkwrap.json", "pom.xml", "build.gradle",
        "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
        "composer.json", "composer.lock",
    }
    excluded = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "vendor", "bin", "obj", "__pycache__"}
    files = []
    for root, directories, filenames in os.walk(project):
        directories[:] = [name for name in directories if name not in excluded]
        for filename in filenames:
            path = Path(root) / filename
            if filename in names or path.suffix in {".sln", ".csproj"}:
                files.append(path)
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(project).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def detect(project: Path, runtime_root: Path) -> dict:
    kinds = project_kinds(project)
    tools = {
        "python": executable("python") or executable("py"),
        "node": executable("node"),
        "npm": executable("npm"),
        "java": executable("java"),
        "maven": executable("mvn"),
        "gradle": executable("gradle"),
        "php": executable("php"),
        "composer": executable("composer"),
        "dotnet": executable("dotnet"),
    }
    required = {
        "python": ["python"],
        "node": ["node", "npm"],
        "java": ["java"],
        "php": ["php", "composer"],
        "dotnet": ["dotnet"],
    }
    if "java" in kinds:
        if (project / "pom.xml").is_file() and not (project / ("mvnw.cmd" if os.name == "nt" else "mvnw")).is_file():
            required["java"].append("maven")
        if any(project.glob("build.gradle*")) and not (project / ("gradlew.bat" if os.name == "nt" else "gradlew")).is_file():
            required["java"].append("gradle")
    missing = sorted({tool for kind in kinds for tool in required[kind] if not tools[tool]})
    return {
        "project": str(project),
        "runtime_root": str(runtime_root),
        "project_kinds": kinds,
        "tools": tools,
        "missing_tools": missing,
    }


def install_tool(tool: str, actions: list[dict], timeout: int) -> bool:
    packages = {
        "python": ("Python.Python.3.11", "python311"),
        "node": ("OpenJS.NodeJS.LTS", "nodejs-lts"),
        "npm": ("OpenJS.NodeJS.LTS", "nodejs-lts"),
        "java": ("EclipseAdoptium.Temurin.17.JDK", "temurin17"),
        "maven": ("Apache.Maven", "maven"),
        "gradle": ("Gradle.Gradle", "gradle"),
        "php": ("PHP.PHP.8.3", "php"),
        "composer": ("Composer.Composer", "composer"),
        "dotnet": ("Microsoft.DotNet.SDK.8", "dotnet-8.0-sdk"),
    }
    winget_package, choco_package = packages[tool]
    if executable("winget"):
        result = run(
            ["winget", "install", "--id", winget_package, "--exact", "--silent", "--accept-package-agreements", "--accept-source-agreements"],
            cwd=None,
            timeout=timeout,
            actions=actions,
        )
        if result.returncode == 0:
            refresh_windows_path()
            return True
    if executable("choco"):
        result = run(["choco", "install", choco_package, "-y"], cwd=None, timeout=timeout, actions=actions)
        if result.returncode == 0:
            refresh_windows_path()
            return True
    if platform.system() != "Windows" and executable("brew"):
        brew_name = {"python": "python@3.11", "node": "node", "npm": "node", "java": "openjdk@17", "maven": "maven", "gradle": "gradle", "php": "php", "composer": "composer", "dotnet": "dotnet"}[tool]
        result = run(["brew", "install", brew_name], cwd=None, timeout=timeout, actions=actions)
        if result.returncode == 0:
            return True
    return False


def ensure(project: Path, runtime_root: Path, timeout: int, actions: list[dict]) -> dict:
    runtime_root.mkdir(parents=True, exist_ok=True)
    detected = detect(project, runtime_root)
    for tool in detected["missing_tools"]:
        install_tool(tool, actions, timeout)
    detected = detect(project, runtime_root)
    if detected["missing_tools"]:
        return {**detected, "status": "failed", "failure": "runtime_installation_failed"}
    fingerprint_path = runtime_root / "dependency-fingerprint.json"
    fingerprint = dependency_fingerprint(project)
    if fingerprint_path.is_file():
        previous = json.loads(fingerprint_path.read_text(encoding="utf-8"))
        kinds = set(detected["project_kinds"])
        runtime_ready = (
            ("python" not in kinds or (runtime_root / "python-venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")).is_file())
            and ("node" not in kinds or (runtime_root / "node-project" / "node_modules").is_dir())
            and ("java" not in kinds or (runtime_root / "m2").is_dir() or (runtime_root / "gradle").is_dir())
            and ("php" not in kinds or (runtime_root / "composer-vendor").is_dir())
            and ("dotnet" not in kinds or (runtime_root / "nuget").is_dir())
        )
        if runtime_ready and previous.get("sha256") == fingerprint and previous.get("project_kinds") == detected["project_kinds"]:
            return {**detected, "status": "ready", "reused": True}

    if "python" in detected["project_kinds"]:
        venv = runtime_root / "python-venv"
        python = detected["tools"]["python"]
        if not (venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")).is_file():
            is_windows_launcher = Path(python).name.lower() in {"py", "py.exe"}
            command = [python, "-3.11", "-m", "venv", str(venv)] if is_windows_launcher else [python, "-m", "venv", str(venv)]
            if run(command, cwd=project, timeout=timeout, actions=actions).returncode:
                return {**detected, "status": "failed", "failure": "python_venv_creation_failed"}
        venv_python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        requirements = project / "requirements.txt"
        if requirements.is_file():
            result = run([str(venv_python), "-m", "pip", "install", "-r", str(requirements)], cwd=project, timeout=timeout, actions=actions)
            if result.returncode:
                return {**detected, "status": "failed", "failure": "python_dependency_install_failed", "python": str(venv_python)}
        detected["python"] = str(venv_python)

    if "node" in detected["project_kinds"]:
        node_runtime = runtime_root / "node-project"
        node_runtime.mkdir(exist_ok=True)
        for name in ("package.json", "package-lock.json", "npm-shrinkwrap.json"):
            source = project / name
            if source.is_file():
                shutil.copy2(source, node_runtime / name)
        npm_command = [detected["tools"]["npm"], "ci"] if (node_runtime / "package-lock.json").is_file() else [detected["tools"]["npm"], "install"]
        if run(npm_command, cwd=node_runtime, timeout=timeout, actions=actions).returncode:
            return {**detected, "status": "failed", "failure": "node_dependency_install_failed"}
        detected["node_modules"] = str(node_runtime / "node_modules")

    if "java" in detected["project_kinds"]:
        if (project / "pom.xml").is_file():
            wrapper = project / ("mvnw.cmd" if os.name == "nt" else "mvnw")
            maven = str(wrapper) if wrapper.is_file() else detected["tools"]["maven"]
            command = [maven, f"-Dmaven.repo.local={runtime_root / 'm2'}", "-DskipTests", "dependency:go-offline"]
            if run(command, cwd=project, timeout=timeout, actions=actions).returncode:
                return {**detected, "status": "failed", "failure": "java_dependency_install_failed"}
        elif any(project.glob("build.gradle*")):
            wrapper = project / ("gradlew.bat" if os.name == "nt" else "gradlew")
            gradle = str(wrapper) if wrapper.is_file() else detected["tools"]["gradle"]
            command = [gradle, "--gradle-user-home", str(runtime_root / "gradle"), "dependencies"]
            if run(command, cwd=project, timeout=timeout, actions=actions).returncode:
                return {**detected, "status": "failed", "failure": "java_dependency_install_failed"}

    if "php" in detected["project_kinds"]:
        php_runtime = runtime_root / "php-project"
        php_runtime.mkdir(exist_ok=True)
        for name in ("composer.json", "composer.lock"):
            source = project / name
            if source.is_file():
                shutil.copy2(source, php_runtime / name)
        env = {**os.environ, "COMPOSER_VENDOR_DIR": str(runtime_root / "composer-vendor")}
        command = [detected["tools"]["composer"], "install", "--no-interaction", "--no-scripts", "--prefer-dist"]
        if run(command, cwd=php_runtime, timeout=timeout, actions=actions, env=env).returncode:
            return {**detected, "status": "failed", "failure": "php_dependency_install_failed"}

    if "dotnet" in detected["project_kinds"]:
        projects = [*project.glob("*.sln"), *project.rglob("*.csproj")]
        if projects:
            result = run([detected["tools"]["dotnet"], "restore", str(projects[0]), "--packages", str(runtime_root / "nuget")], cwd=project, timeout=timeout, actions=actions)
            if result.returncode:
                return {**detected, "status": "failed", "failure": "dotnet_restore_failed"}

    fingerprint_path.write_text(json.dumps({"sha256": fingerprint, "project_kinds": detected["project_kinds"]}, indent=2) + "\n", encoding="utf-8")
    detected["status"] = "ready"
    return detected


def verify(project: Path, runtime_root: Path, timeout: int, actions: list[dict]) -> dict:
    detected = detect(project, runtime_root)
    checks = []
    python = runtime_root / "python-venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if "python" in detected["project_kinds"]:
        result = run([str(python), "-m", "pip", "check"], cwd=project, timeout=timeout, actions=actions)
        checks.append({"name": "python_dependency_consistency", "status": "passed" if result.returncode == 0 else "failed"})
        detected["python"] = str(python)
    if "node" in detected["project_kinds"]:
        result = run([detected["tools"]["npm"], "list", "--prefix", str(runtime_root / "node-project"), "--depth=0"], cwd=project, timeout=timeout, actions=actions)
        checks.append({"name": "node_dependency_consistency", "status": "passed" if result.returncode == 0 else "failed"})
    if "java" in detected["project_kinds"]:
        result = run([detected["tools"]["java"], "-version"], cwd=project, timeout=timeout, actions=actions)
        checks.append({"name": "java_runtime", "status": "passed" if result.returncode == 0 else "failed"})
        cache_ready = (runtime_root / "m2").is_dir() or (runtime_root / "gradle").is_dir()
        checks.append({"name": "java_dependencies_external", "status": "passed" if cache_ready else "failed"})
    if "php" in detected["project_kinds"]:
        result = run([detected["tools"]["composer"], "validate", "--no-interaction"], cwd=runtime_root / "php-project", timeout=timeout, actions=actions)
        checks.append({"name": "php_dependency_consistency", "status": "passed" if result.returncode == 0 and (runtime_root / "composer-vendor").is_dir() else "failed"})
    if "dotnet" in detected["project_kinds"]:
        projects = [*project.glob("*.sln"), *project.rglob("*.csproj")]
        result = run([detected["tools"]["dotnet"], "restore", str(projects[0]), "--packages", str(runtime_root / "nuget")], cwd=project, timeout=timeout, actions=actions)
        checks.append({"name": "dotnet_dependency_consistency", "status": "passed" if result.returncode == 0 else "failed"})
    if not detected["project_kinds"]:
        checks.append({"name": "no_managed_runtime_required", "status": "passed"})
    detected["checks"] = checks
    detected["status"] = "ready" if not detected["missing_tools"] and all(item["status"] == "passed" for item in checks) else "failed"
    return detected


def main() -> int:
    args = parse_args()
    project = Path(args.project).expanduser().resolve()
    runtime_root = Path(args.runtime_root).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not project.is_dir():
        raise SystemExit(f"Project directory does not exist: {project}")
    if project == runtime_root or project in runtime_root.parents or runtime_root in project.parents:
        raise SystemExit("runtime-root must be outside the project source tree")
    actions: list[dict] = []
    if args.command == "detect":
        result = detect(project, runtime_root)
        result["status"] = "ready" if not result["missing_tools"] else "needs_setup"
    elif args.command == "ensure":
        result = ensure(project, runtime_root, args.timeout, actions)
        if result.get("status") == "ready":
            result = verify(project, runtime_root, args.timeout, actions)
    else:
        result = verify(project, runtime_root, args.timeout, actions)
    report = {
        "$schema": SCHEMA,
        "command": args.command,
        "project": str(project),
        "runtime_root": str(runtime_root),
        "status": result.get("status", "failed"),
        "project_kinds": result.get("project_kinds", []),
        "tools": result.get("tools", {}),
        "resolved": {key: value for key, value in result.items() if key in {"python", "node_modules"}},
        "missing_tools": result.get("missing_tools", []),
        "checks": result.get("checks", []),
        "failure": result.get("failure", ""),
        "actions": actions,
        "updated_at": utc_now(),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"ready", "needs_setup"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

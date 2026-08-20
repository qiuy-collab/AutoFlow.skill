#!/usr/bin/env python3
"""
AutoFlow environment check & auto-install (check + supply).

Usage:
    python env_setup.py              # check + auto-install missing deps
    python env_setup.py --check-only # only check, no install
    python env_setup.py --route ai             # install deps for a specific module action
    python env_setup.py --route diagram
    python env_setup.py --route all            # install everything (default)
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional


SKILL_ROOT = Path(__file__).resolve().parent.parent

# ── colour helpers ────────────────────────────────────────────────────────────
try:
    import colorama
    colorama.init()
    RED, GREEN, YELLOW, CYAN, RESET = (
        colorama.Fore.RED, colorama.Fore.GREEN,
        colorama.Fore.YELLOW, colorama.Fore.CYAN,
        colorama.Style.RESET_ALL
    )
except ImportError:
    RED = GREEN = YELLOW = CYAN = RESET = ""


def ok(msg: str) -> None:
    print(f"{GREEN}[OK]    {msg}{RESET}")

def warn(msg: str) -> None:
    print(f"{YELLOW}[WARN]  {msg}{RESET}")

def fail(msg: str) -> None:
    print(f"{RED}[FAIL]  {msg}{RESET}")

def fix(msg: str) -> None:
    print(f"{CYAN}[FIX]   {msg}{RESET}")

def log(msg: str) -> None:
    print(f"        {msg}")


# ── phase 0: python ───────────────────────────────────────────────────────────
def check_python() -> bool:
    if not shutil.which("python"):
        fail("python not found on PATH — cannot auto-fix, install Python first")
        return False
    try:
        ver = subprocess.check_output([sys.executable, "--version"], text=True, stderr=subprocess.STDOUT).strip()
        ok(f"python: {ver}")
        return True
    except Exception:
        fail("python --version failed")
        return False


# ── phase 1: pip packages ─────────────────────────────────────────────────────
def run_pip_install(packages: List[str], label: str) -> bool:
    """pip install a list of packages; return True if all succeed."""
    needed = []
    for pkg in packages:
        pkg_name = pkg.split("==")[0].split(">")[0].split("<")[0].strip()
        try:
            __import__(pkg_name.replace("-", "_"))
            ok(f"pip package available: {pkg}")
        except ImportError:
            needed.append(pkg)

    if not needed:
        return True

    fix(f"installing: {' '.join(needed)} ({label})")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + needed,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        ok(f"{label} installed")
        return True
    except subprocess.CalledProcessError:
        fail(f"{label} install failed — try: pip install {' '.join(needed)}")
        return False


PIP_REQUIRED = ["requests", "python-docx", "Pillow"]
PIP_BROWSER = ["playwright"]
PIP_CHART = ["numpy", "matplotlib"]
PIP_VIDEO = ["av", "opencv-python", "numpy", "mss"]
PIP_ALL = list(set(PIP_REQUIRED + PIP_BROWSER + PIP_CHART + PIP_VIDEO))


def install_playwright_browsers() -> bool:
    """Install Chromium for Playwright after pip install."""
    try:
        from playwright.sync_api import sync_playwright
        ok("playwright module available")
    except ImportError:
        return False

    if (Path(sys.prefix) / "Library" / "ms-playwright" / "chromium-1091").exists():
        ok("playwright chromium browser already installed")
        return True

    fix("installing playwright chromium browser...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        ok("playwright chromium installed")
        return True
    except subprocess.CalledProcessError:
        warn("playwright chromium install failed — image.capture may not work without it")
        return False


# ── phase 2: DSL renderers ────────────────────────────────────────────────────
def _check_cmd(cmd: str, friendly: str, install_hint: str, auto_install: Optional[List[str]] = None) -> bool:
    """Check if a CLI tool exists; optionally auto-install."""
    if shutil.which(cmd):
        ok(f"{friendly} available: {shutil.which(cmd)}")
        return True

    warn(f"{friendly} not found")
    if auto_install:
        fix(f"auto-installing: {' '.join(auto_install)}")
        try:
            subprocess.check_call(auto_install)
            if shutil.which(cmd):
                ok(f"{friendly} installed successfully")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    warn(f"{friendly} unavailable — image.diagram needs it")
    log(f"  manual install: {install_hint}")
    return False


def check_dsl_tools(dry_run: bool = False) -> dict:
    """Check Mermaid CLI, D2, PlantUML. Return dict of available tools."""
    result = {"mmdc": False, "d2": False, "plantuml": False}

    if dry_run:
        return result

    # mmdc
    if shutil.which("mmdc"):
        ok("Mermaid CLI (mmdc) available")
        result["mmdc"] = True
    else:
        warn("Mermaid CLI (mmdc) not found")
        if os.name == "nt":
            fix("auto-installing: npm install -g @mermaid-js/mermaid-cli")
            try:
                subprocess.check_call(["npm", "install", "-g", "@mermaid-js/mermaid-cli"],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if shutil.which("mmdc"):
                    ok("mmdc installed")
                    result["mmdc"] = True
            except Exception:
                log("  manual: npm install -g @mermaid-js/mermaid-cli")
        else:
            log("  manual: npm install -g @mermaid-js/mermaid-cli")

    # d2
    if shutil.which("d2"):
        ok("D2 available")
        result["d2"] = True
    else:
        warn("D2 not found")
        log("  manual: winget install Terrastruct.D2  or  https://d2lang.com/tour/install")

    # plantuml
    if shutil.which("plantuml"):
        ok("PlantUML available")
        result["plantuml"] = True
    else:
        warn("PlantUML not found")
        if shutil.which("java"):
            log("  java is available; download plantuml.jar from https://plantuml.com/download")
        else:
            warn("  java not found — PlantUML requires Java")
            log("  manual: winget install OpenJDK.OpenJDK.17  then install PlantUML")

    return result


# ── phase 3: integrated and optional Skill capabilities ──────────────────────
SKILL_NAMES: list[str] = []
INTEGRATED_PATHS = {
    "impeccable": SKILL_ROOT / "integrations" / "impeccable" / "SKILL.md",
}


def find_skill_file(name: str):
    candidates = [
        Path.home() / ".codex" / "skills" / name / "SKILL.md",
        Path.home() / ".agents" / "skills" / name / "SKILL.md",
    ]
    return next((path for path in candidates if path.is_file()), None)


def check_skill_capabilities() -> bool:
    for name, skill_file in INTEGRATED_PATHS.items():
        if skill_file.is_file():
            ok(f"integrated capability: {name} ({skill_file})")
        else:
            warn(f"integrated capability missing: {name}; dependent workflows will stop at PLAN")
    for name in SKILL_NAMES:
        skill_file = find_skill_file(name)
        if skill_file:
            ok(f"skill capability: {name} ({skill_file})")
        else:
            warn(f"optional skill capability missing: {name}; workflows that need it will stop at PLAN")
    return True


# ── phase 4: .env ─────────────────────────────────────────────────────────────
def check_dotenv() -> bool:
    env_path = SKILL_ROOT / ".env"
    env_example = SKILL_ROOT / ".env.example"

    if not env_path.exists():
        warn(".env missing — image.ai needs BASEURL + APIKEY")
        if env_example.exists():
            try:
                shutil.copy(env_example, env_path)
                fix(".env.example copied to .env — fill in BASEURL + APIKEY")
            except Exception:
                warn("could not copy .env.example; create .env manually")
        else:
            warn("create .env with: BASEURL=https://your-api  APIKEY=sk-xxx")
        return False

    # parse .env
    env_vars = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip()

    baseurl = env_vars.get("BASEURL", "").strip()
    apikey = env_vars.get("APIKEY", "").strip()

    if baseurl and apikey:
        ok(".env contains BASEURL + APIKEY")
        return True
    elif baseurl or apikey:
        warn(".env has incomplete API keys — image.ai may not work")
        return False
    else:
        warn(".env exists but BASEURL/APIKEY are empty — fill them in")
        return False


# ── phase 5: upstream probe (optional) ────────────────────────────────────────
def probe_upstream() -> bool:
    """Quick upstream probe if BASEURL/APIKEY are configured."""
    probe_script = SKILL_ROOT / "scripts" / "generate_images.py"
    if not probe_script.exists():
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(probe_script), "--check"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            ok("upstream image API probe passed")
            return True
        else:
            warn("upstream image API probe failed — check BASEURL/APIKEY in .env")
            return False
    except (subprocess.TimeoutExpired, Exception):
        warn("upstream probe timed out or failed")
        return False


# ── main ──────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="AutoFlow environment check & auto-install")
    parser.add_argument("--check-only", action="store_true",
                        help="Only check, do not install anything")
    parser.add_argument("--route", choices=["ai", "capture", "diagram", "chart", "video", "all"],
                        default="all", help="Target route (default: all)")
    parser.add_argument("--no-probe", action="store_true",
                        help="Skip upstream API probe")
    return parser.parse_args()


def main():
    args = parse_args()
    dry_run = args.check_only
    route = args.route

    print("=" * 50)
    print("AutoFlow Environment Setup (check + supply)")
    print(f"Root: {SKILL_ROOT}")
    print(f"Mode: {'check-only' if dry_run else 'auto-install'}")
    print(f"Route: {route}")
    print("=" * 50)
    print()

    overall = True

    # ── 0: python ──
    print("── Python ──")
    if not check_python():
        fail("Cannot proceed without Python")
        sys.exit(1)
    print()

    # ── 1: pip packages ──
    print("── pip packages ──")
    if not dry_run:
        run_pip_install(PIP_REQUIRED, "required")

    if route in ("capture", "all"):
        if not dry_run:
            run_pip_install(PIP_BROWSER, "image.capture")
            install_playwright_browsers()

    if route in ("chart", "all"):
        if not dry_run:
            run_pip_install(PIP_CHART, "image.chart")

    if route in ("video", "all"):
        if not dry_run:
            run_pip_install(PIP_VIDEO, "video")
    print()

    # ── 2: DSL tools ──
    if route in ("diagram", "all"):
        print("── DSL renderers ──")
        check_dsl_tools(dry_run=dry_run)
        print()

    # ── 3: Skill capabilities ──
    print("── Skill capabilities ──")
    if not check_skill_capabilities():
        overall = False
    print()

    # ── 4: .env ──
    print("── .env ──")
    check_dotenv()
    print()

    # ── 5: upstream probe ──
    if route in ("ai", "all") and not args.no_probe:
        print("── upstream probe ──")
        probe_upstream()
        print()

    # ── summary ──
    print("=" * 50)
    if overall:
        ok("Environment setup complete")
    else:
        warn("Environment setup done with warnings — review above")
    print("=" * 50)


if __name__ == "__main__":
    main()

import argparse
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Capture local frontend screenshots for AutoFlow.")
    parser.add_argument("--config", required=True, help="Path to the browser capture plan JSON")
    parser.add_argument("--output-dir", required=True, help="Directory for captured screenshots")
    parser.add_argument("--timeout-seconds", type=int, default=45, help="Server startup timeout")
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_log_tail(log_path: Path, max_chars: int = 1200):
    if not log_path.exists():
        return ""
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    return text[-max_chars:]


def choose_browser_executable():
    for candidate in BROWSER_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    raise SystemExit("No supported Chrome/Edge executable found for browser capture")


def normalize_target_url(base_url: str, target: str):
    value = (target or "").strip()
    if not value:
        return base_url
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.startswith("/"):
        return base_url.rstrip("/") + value
    return base_url.rstrip("/") + "/" + value.lstrip("/")


def resolve_input_file(plan, value: str) -> str:
    candidate = Path((value or "").strip()).expanduser()
    if not candidate.is_absolute():
        startup_cwd = plan.get("startup_cwd", "").strip()
        base = Path(startup_cwd) if startup_cwd else Path.cwd()
        candidate = (base / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.exists():
        raise SystemExit(f"Browser capture upload file does not exist: {candidate}")
    return str(candidate)


def wait_for_url(url: str, timeout_seconds: int, process=None, log_path: Path | None = None):
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        if process is not None and process.poll() is not None:
            tail = read_log_tail(log_path) if log_path else ""
            raise SystemExit(
                f"Local frontend process exited before the page became available: {url}\n"
                f"Exit code: {process.returncode}\n"
                f"Startup log tail:\n{tail}"
            )
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status < 500:
                    return
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    tail = read_log_tail(log_path) if log_path else ""
    raise SystemExit(
        f"Timed out waiting for local frontend to become available: {url}\n"
        f"Last error: {last_error}\n"
        f"Startup log tail:\n{tail}"
    )


def start_local_app(plan, timeout_seconds: int):
    command = plan.get("startup_command", "").strip()
    if not command:
        return None, None
    cwd = plan.get("startup_cwd", "").strip() or None
    log_path = Path(plan.get("startup_log_path") or Path(cwd or Path.cwd()) / "autoflow_browser_startup.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(command, cwd=cwd, shell=True, stdout=log_handle, stderr=subprocess.STDOUT)
    wait_for_url(plan["base_url"], timeout_seconds, process=process, log_path=log_path)
    log_handle.close()
    return process, log_path


def stop_local_app(process):
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()


def normalize_url(plan, shot):
    if shot.get("full_url"):
        return shot["full_url"]
    base_url = plan["base_url"].rstrip("/")
    path = shot.get("url_path", "").strip()
    if not path:
        return base_url
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return base_url + path


def run_action(page, action, plan):
    action_type = action.get("type")
    selector = action.get("selector")
    value = action.get("value")
    if action_type == "goto":
        page.goto(normalize_target_url(plan["base_url"], value), wait_until="networkidle")
    elif action_type == "click":
        page.locator(selector).click()
    elif action_type == "fill":
        page.locator(selector).fill(value)
    elif action_type in {"set_input_files", "upload_file"}:
        page.locator(selector).set_input_files(resolve_input_file(plan, value))
    elif action_type == "press":
        page.locator(selector).press(value)
    elif action_type == "hover":
        page.locator(selector).hover()
    elif action_type == "check":
        page.locator(selector).check()
    elif action_type == "select_option":
        page.locator(selector).select_option(value)
    elif action_type == "wait_for_selector":
        page.locator(selector).first.wait_for()
    elif action_type == "wait_for_timeout":
        page.wait_for_timeout(int(value))
    else:
        raise SystemExit(f"Unsupported browser capture action type: {action_type}")


def capture_screenshots(images_dir: Path, plan):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Browser capture requires Playwright. Install the optional browser backend "
            "before executing capture_frontend_screenshots.py."
        ) from exc

    images_dir.mkdir(parents=True, exist_ok=True)
    executable = choose_browser_executable()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.25)
        page = context.new_page()
        for shot in plan.get("screenshots", []):
            page.goto(normalize_url(plan, shot), wait_until="networkidle")
            for action in shot.get("actions", []):
                run_action(page, action, plan)
            if shot.get("wait_after_actions_ms"):
                page.wait_for_timeout(int(shot["wait_after_actions_ms"]))
            target = images_dir / f"{shot['name']}.png"
            page.screenshot(path=str(target), full_page=bool(shot.get("full_page", True)))
            print(f"Captured browser screenshot: {target}")
        context.close()
        browser.close()


def main():
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    plan = load_json(config_path)
    images_dir = Path(args.output_dir).expanduser().resolve()

    if not plan.get("enabled", False):
        raise SystemExit("browser_capture_plan.json is not enabled")
    if not plan.get("screenshots"):
        raise SystemExit("browser_capture_plan.json has no screenshots to capture")

    process = None
    try:
        process, _ = start_local_app(plan, args.timeout_seconds)
        capture_screenshots(images_dir, plan)
    finally:
        stop_local_app(process)


if __name__ == "__main__":
    main()

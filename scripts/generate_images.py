import base64
import json
import re
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

warnings.filterwarnings("ignore")

import requests
from requests.exceptions import RequestsDependencyWarning

warnings.filterwarnings("ignore", category=RequestsDependencyWarning)


print_lock = threading.Lock()


def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_env_file() -> dict:
    env_path = skill_root() / ".env"
    env_vars: dict = {}
    if not env_path.exists():
        return env_vars

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        delimiter = "=" if "=" in line else ":" if ":" in line else None
        if delimiter is None:
            continue
        key, value = line.split(delimiter, 1)
        env_vars[key.strip()] = value.strip()
    return env_vars


env_vars = load_env_file()


def parse_upstreams() -> Tuple[List[str], List[str], int]:
    baseurls_csv = env_vars.get("BASEURLS", "").strip()
    apikeys_csv = env_vars.get("APIKEYS", "").strip()
    if baseurls_csv and apikeys_csv:
        baseurls = [u.strip() for u in baseurls_csv.split(",") if u.strip()]
        apikeys = [k.strip() for k in apikeys_csv.split(",") if k.strip()]
        count = min(len(baseurls), len(apikeys))
        if count > 0:
            return baseurls[:count], apikeys[:count], count

    idx = 1
    numbered_baseurls = []
    numbered_apikeys = []
    while True:
        bu = env_vars.get(f"BASEURL{idx}", "").strip()
        ak = env_vars.get(f"APIKEY{idx}", "").strip()
        if not bu or not ak:
            break
        numbered_baseurls.append(bu)
        numbered_apikeys.append(ak)
        idx += 1
    if numbered_baseurls:
        return numbered_baseurls, numbered_apikeys, len(numbered_baseurls)

    single_url = env_vars.get("BASEURL", "").strip()
    single_key = env_vars.get("APIKEY", "").strip()
    if single_url and single_key:
        return [single_url], [single_key], 1

    return [], [], 0


DEFAULT_POLICY = {
    "default_mode": "generic",
    "auto_append_negative": True,
    "fail_on_prompt_risk": True,
    "probe_retries": 3,
    "probe_timeout": 180,
    "batch_timeout": 180,
    "skip_existing_files": True,
    "forbidden_terms": [
        "娴佺▼鍥?",
        "鏋舵瀯鍥?",
        "绠ご鏍囨敞",
        "璁茶В鏉?",
        "璇存槑闈㈡澘",
        "鎮诞鏍囨敞",
        "poster",
        "callout",
        "annotation",
        "flowchart",
        "diagram",
    ],
    "ui_density": "low_information_density",
    "crop_browser_chrome": True,
    "forbid_localhost_or_dev_url": True,
    "quality_constraints": {
        "consistency": True,
        "pixel_sharpness": True,
        "no_blur_or_mosaic": True,
        "time_consistency": True,
    },
}

RESOLUTION_ALIASES = {
    "2k_16_9": "2048x1152",
    "2K 16:9": "2048x1152",
    "4k_16_9": "3840x2160",
    "4K 16:9": "3840x2160",
}

SCREENSHOT_NEGATIVE_PROMPT = (
    "Only show content that could naturally appear in a real screen capture. "
    "Do not add explanatory text panels, poster layouts, arrows, flowcharts, split-screen teaching boards, "
    "captions outside the program window, or decorative annotations. "
    "Text may appear only where a real operating system, terminal, IDE, or application would naturally render it. "
    "Show only the necessary information, keep a believable background, avoid high information density, avoid tiny unreadable text, "
    "avoid localhost, 127.0.0.1, dev server URLs, browser address bars, tabs, and malformed UI details."
)

SCREENSHOT_QUALITY_PROMPT = (
    "Ensure pixel-level sharpness and crisp text rendering. "
    "No blur, no smeared text, no mosaic, no blocky compression artifacts, and no warped UI edges. "
    "Keep the same visual environment, lighting, UI style, and rendering fidelity across the full image set. "
    "If clocks, timestamps, or time indicators appear, keep them realistic and temporally consistent with the same session."
)


def normalize_policy(config: dict) -> dict:
    policy = dict(DEFAULT_POLICY)
    policy.update(config.get("image_policy", {}))
    quality = dict(DEFAULT_POLICY.get("quality_constraints", {}))
    quality.update(config.get("image_policy", {}).get("quality_constraints", {}))
    policy["quality_constraints"] = quality
    return policy


def normalize_resolution(value: str) -> str:
    return RESOLUTION_ALIASES.get(str(value).strip(), str(value).strip())


def lint_prompt(policy: dict, image_name: str, prompt: str, mode: str) -> List[str]:
    if mode != "screenshot_strict":
        return []
    lower_prompt = prompt.lower()
    hits = []
    for term in policy.get("forbidden_terms", []):
        lower_term = term.lower()
        if lower_term not in lower_prompt:
            continue
        idx = lower_prompt.find(lower_term)
        window_start = max(0, idx - 60)
        context_en = lower_prompt[window_start:idx]
        context_zh = prompt[max(0, idx - 12):idx]
        if any(marker in context_en for marker in [" no ", " not ", " without ", "do not add", "don't add", "avoid ", "avoid any "]):
            continue
        if any(marker in context_zh for marker in ["涓嶈", "涓嶈鏈?", "涓嶈兘鏈?", "鏃?"]):
            continue
        hits.append(term)
    return [f"{image_name}: screenshot_strict prompt contains forbidden term '{term}'" for term in hits]


def build_full_prompt(global_prompt: str, image_prompt: str, policy: dict, mode: str) -> str:
    parts: List[str] = []
    if global_prompt:
        parts.append(global_prompt.strip())
    if image_prompt:
        parts.append(image_prompt.strip())
    if mode == "screenshot_strict" and policy.get("auto_append_negative", True):
        if policy.get("ui_density") == "low_information_density":
            parts.append("Keep the interface information density low. Show only necessary panels and a believable surrounding background.")
        if policy.get("crop_browser_chrome", False):
            parts.append("Do not show browser tabs, browser address bar, or system chrome unless absolutely necessary.")
        if policy.get("forbid_localhost_or_dev_url", False):
            parts.append("Do not show localhost, 127.0.0.1, dev server URLs, or temporary local addresses anywhere in the image.")
        quality = policy.get("quality_constraints", {})
        quality_fragments = []
        if quality.get("consistency", True):
            quality_fragments.append("Keep the full image set visually consistent across environment, camera angle style, and UI treatment.")
        if quality.get("pixel_sharpness", True):
            quality_fragments.append("Maintain pixel-level sharpness with crisp readable text and clean edges.")
        if quality.get("no_blur_or_mosaic", True):
            quality_fragments.append("Do not introduce blur, soft-focus haze, mosaic blocks, compression squares, or smeared glyphs.")
        if quality.get("time_consistency", True):
            quality_fragments.append("If any time or date is visible, keep it realistic and consistent with the same operation session.")
        if quality_fragments:
            parts.append(" ".join(quality_fragments))
            parts.append(SCREENSHOT_QUALITY_PROMPT)
        parts.append(SCREENSHOT_NEGATIVE_PROMPT)
    return ", ".join(part for part in parts if part)


def resolve_output_dir(config_path: Path, configured_output_dir: Optional[str]) -> Path:
    if configured_output_dir:
        output_path = Path(configured_output_dir).expanduser()
        if not output_path.is_absolute():
            # Resolve relative paths against CWD (project root), NOT config_path.parent.
            # This prevents path doubling when config is inside a project subdirectory.
            output_path = (Path.cwd() / output_path).resolve()
        else:
            output_path = output_path.resolve()
        return output_path

    output_dir = config_path.parent / "generated_images"
    if (config_path.parent / "workflow.json").exists():
        return output_dir.resolve()

    raise SystemExit(
        f"prompt_config.json must have an explicit 'output_dir' field.\n"
        f"Current config: {config_path}\n"
        f"Expected: inside an init_run.py output directory with workflow.json.\n"
        f"Fix: set 'output_dir' in prompt_config.json to the correct project images directory."
    )


def shard_tasks_for_upstream(tasks: list, upstream_index: int, upstream_count: int) -> list:
    return [t for t in tasks if t["index"] % upstream_count == upstream_index]


def build_supplement_config(config: dict, image_names: List[str], output_path: Path, reason: str) -> Optional[Path]:
    if not image_names:
        return None
    target_names = set(image_names)
    selected = [item for item in config.get("images", []) if item.get("name") in target_names]
    if not selected:
        return None

    supplement = dict(config)
    supplement["images"] = selected
    supplement["total_count"] = len(selected)
    supplement["source_config"] = str(output_path.parent / "prompt_config.json")
    supplement["supplement_reason"] = reason
    supplement["supplement_image_names"] = image_names
    output_path.write_text(json.dumps(supplement, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def write_generation_report(config_path: Path, output_dir: Path, results: List[Dict], config: dict) -> None:
    report_path = config_path.parent / "image_generation_report.json"
    failed_names = [item["name"] for item in results if not item.get("success")]
    skipped_names = [item["name"] for item in results if item.get("skipped")]
    report = {
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "total_results": len(results),
        "success_count": sum(1 for item in results if item.get("success")),
        "failed_count": len(failed_names),
        "skipped_count": len(skipped_names),
        "failed_image_names": failed_names,
        "skipped_image_names": skipped_names,
        "results": results,
    }

    supplement_path = config_path.parent / "prompt_config.supplement.json"
    built = build_supplement_config(config, failed_names, supplement_path, "failed_images_only")
    if built:
        report["supplement_config_path"] = str(built)

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    safe_print(f"generation report: {report_path}")
    if built:
        safe_print(f"supplement config for failed images: {built}")


def encode_ref_image(ref_image_path: str) -> Optional[str]:
    """Encode a local image file to base64 data URI for img2img API.

    Returns None if the file doesn't exist or can't be read.
    """
    path = Path(ref_image_path).expanduser().resolve()
    if not path.exists():
        safe_print(f"[WARN] Reference image not found: {path}")
        return None
    try:
        raw = path.read_bytes()
        ext = path.suffix.lower().lstrip(".")
        mime_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        mime = mime_map.get(ext, "image/png")
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception as exc:
        safe_print(f"[WARN] Failed to encode reference image {path}: {exc}")
        return None


def _pad_to_square(image_path: Path, target_size: int | None = None) -> tuple[Path, int]:
    """Pad a non-square image to square with edge-mirror padding (no resize by default).

    Uses ImageFilter.BoxBlur on the mirrored edge to create a seamless transition,
    preventing the AI model from hallucinating artifacts in the padding area.

    Args:
        image_path: Path to the input image.
        target_size: If provided, also resize the padded square to this size (e.g. 1024).
                     If None, keeps the native max(W,H) as the square side.

    Returns:
        (padded_path, square_side) — path to temp PNG and the actual pixel dimension.
    """
    from PIL import Image, ImageFilter

    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    side = max(w, h)

    # Create canvas filled with edge-mirror pattern (not pure black)
    # to prevent AI hallucination artifacts
    canvas = Image.new("RGB", (side, side))

    if w == h:
        # Already square — center it directly
        canvas.paste(img, (0, 0))
    else:
        # Paste original centered on canvas
        paste_x = (side - w) // 2
        paste_y = (side - h) // 2
        canvas.paste(img, (paste_x, paste_y))

        # Fill padding areas with a blurred extension of the nearest edge
        # to create a natural-looking border instead of harsh black bars
        if h > w:
            # Vertical bars on left/right — extend leftmost/rightmost columns
            left_strip = img.crop((0, 0, 1, h)).resize((paste_x, h), Image.NEAREST)
            right_strip = img.crop((w - 1, 0, w, h)).resize((side - paste_x - w, h), Image.NEAREST)
            left_blurred = left_strip.filter(ImageFilter.BoxBlur(max(paste_x // 4, 2)))
            right_blurred = right_strip.filter(ImageFilter.BoxBlur(max((side - paste_x - w) // 4, 2)))
            canvas.paste(left_blurred, (0, paste_y))
            canvas.paste(right_blurred, (paste_x + w, paste_y))
        else:
            # Horizontal bars on top/bottom — extend topmost/bottommost rows
            top_strip = img.crop((0, 0, w, 1)).resize((w, paste_y), Image.NEAREST)
            bottom_strip = img.crop((0, h - 1, w, h)).resize((w, side - paste_y - h), Image.NEAREST)
            top_blurred = top_strip.filter(ImageFilter.BoxBlur(max(paste_y // 4, 2)))
            bottom_blurred = bottom_strip.filter(ImageFilter.BoxBlur(max((side - paste_y - h) // 4, 2)))
            canvas.paste(top_blurred, (paste_x, 0))
            canvas.paste(bottom_blurred, (paste_x, paste_y + h))

    if target_size and target_size != side:
        canvas = canvas.resize((target_size, target_size), Image.LANCZOS)
        side = target_size

    # Save to temp PNG
    tmp_path = image_path.parent / f".{image_path.stem}_square_padded.png"
    canvas.save(tmp_path, "PNG")
    return tmp_path, side


def _call_img2img_edits(
    prompt: str,
    ref_image_path: str,
    output_dir: str,
    filename: str,
    resolution: str,  # kept in signature for compatibility, ignored internally
    base_url: str,
    api_key: str,
    timeout: int,
    silent: bool,
) -> Optional[str]:
    """Call /v1/images/edits endpoint for img2img (multipart form upload).

    Sends the original reference image as-is — no padding, no preprocessing.
    The API's ``size`` parameter controls output resolution; it handles
    non-square input aspect ratios internally.  Padding was avoided because
    it inflated file size and caused ConnectionReset on some proxy APIs.
    """
    url = f"{base_url.rstrip('/')}/v1/images/edits"
    path = Path(ref_image_path).expanduser().resolve()
    if not path.exists():
        if not silent:
            safe_print(f"[WARN] Reference image not found: {path}")
        return None

    try:
        if not silent:
            safe_print(f"[img2img] {path.name} ({path.stat().st_size:,} bytes) → API")

        with path.open("rb") as fh:
            files = {"image": (path.name, fh, "image/png")}
            data = {
                "prompt": prompt,
                "model": "gpt-image-2",
                "n": "1",
                "size": "1024x1024",
            }
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.post(url, files=files, data=data, headers=headers, timeout=timeout)
            response.raise_for_status()

        result = response.json()
        if "data" not in result or not result["data"]:
            if not silent:
                safe_print(f"[img2img] Unexpected response (no data): {result}")
            return None

        return _save_img2img_result(result, output_dir, filename, silent)

    except requests.exceptions.Timeout:
        if not silent:
            safe_print(f"[TIMEOUT] img2img edits timed out after {timeout}s")
        return None
    except requests.exceptions.ConnectionError as exc:
        if not silent:
            safe_print(f"[CONNECT ERROR] img2img edits: {exc}")
        return None
    except Exception as exc:
        if not silent:
            safe_print(f"[img2img] Error: {exc}")
        return None


def _save_img2img_result(result: dict, output_dir: str, filename: str, silent: bool) -> Optional[str]:
    """Save the result image from an img2img edits API response."""
    image_data = result["data"][0]
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{filename}.png"

    if "url" in image_data:
        image_response = requests.get(image_data["url"], timeout=30)
        image_response.raise_for_status()
        file_path.write_bytes(image_response.content)
        return str(file_path)

    if "b64_json" in image_data:
        file_path.write_bytes(base64.b64decode(image_data["b64_json"]))
        return str(file_path)

    if not silent:
        safe_print("img2img edits response did not contain image data")
    return None


def generate_image_single(
    prompt: str,
    output_dir: Optional[str] = None,
    resolution: str = "1024x1024",
    filename: Optional[str] = None,
    silent: bool = False,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    upstream_index: Optional[int] = None,
    timeout: int = 120,
    ref_image: Optional[str] = None,
):
    """Generate a single image. Set ref_image to a local file path for img2img mode (uses /v1/images/edits)."""
    resolution = normalize_resolution(resolution)

    if not base_url or not api_key:
        baseurls, apikeys, count = parse_upstreams()
        if upstream_index is not None and upstream_index < count:
            base_url = baseurls[upstream_index]
            api_key = apikeys[upstream_index]
        elif count > 0:
            base_url = baseurls[0]
            api_key = apikeys[0]

    if not base_url or not api_key:
        if not silent:
            safe_print("Missing BASEURL or APIKEY in .env")
        return None

    if not output_dir:
        raise SystemExit("output_dir is required for image generation - refusing to use CWD as fallback.")
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    # --- img2img: route to /v1/images/edits (multipart form) ---
    if ref_image:
        return _call_img2img_edits(
            prompt=prompt,
            ref_image_path=ref_image,
            output_dir=str(output_path),
            filename=filename or generate_filename_from_prompt(prompt).replace(".png", ""),
            resolution=resolution,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            silent=silent,
        )

    # --- txt2img: /v1/images/generations (JSON body) ---
    url = f"{base_url.rstrip('/')}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data: dict = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": 1,
        "size": resolution,
        "quality": "high",
    }

    if not silent:
        safe_print(f"Generating image with prompt: {prompt}")
        safe_print(f"API endpoint: {url}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.Timeout:
        if not silent:
            safe_print(f"[TIMEOUT] API request timed out after {timeout}s: {url}")
        return None
    except requests.exceptions.ConnectionError as exc:
        if not silent:
            safe_print(f"[CONNECT ERROR] Cannot reach API: {exc}")
        return None
    except requests.exceptions.HTTPError as exc:
        if not silent:
            safe_print(f"[HTTP ERROR] API returned error: {exc}")
        return None

    if "data" not in result or not result["data"]:
        if not silent:
            safe_print(f"Unexpected response: {result}")
        return None

    image_data = result["data"][0]
    file_path = output_path / f"{filename}.png" if filename else output_path / generate_filename_from_prompt(prompt)

    if "url" in image_data:
        image_response = requests.get(image_data["url"], timeout=30)
        image_response.raise_for_status()
        file_path.write_bytes(image_response.content)
        return str(file_path)

    if "b64_json" in image_data:
        import base64 as _b64

        file_path.write_bytes(_b64.b64decode(image_data["b64_json"]))
        return str(file_path)

    if not silent:
        safe_print("Response did not contain image data")
    return None


def probe_upstream_once(base_url: str, api_key: str, timeout: int) -> Tuple[bool, str]:
    url = f"{base_url.rstrip('/')}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-image-2",
        "prompt": "generate a small dog image",
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.Timeout:
        return False, f"timeout after {timeout}s"
    except requests.exceptions.ConnectionError as exc:
        return False, f"connection error: {exc}"
    except requests.exceptions.HTTPError as exc:
        return False, f"http error: {exc}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

    data_items = result.get("data") or []
    if not data_items:
        return False, "response has no data items"
    first = data_items[0]
    if first.get("url") or first.get("b64_json"):
        return True, "valid image payload received"
    return False, "response data missing url/b64_json"


def generate_image_task(task_info: dict) -> Dict:
    index = task_info["index"]
    total = task_info["total"]
    name = task_info["name"]
    prompt = task_info["prompt"]
    output_dir = task_info["output_dir"]
    resolution = task_info["resolution"]
    max_retries = task_info.get("max_retries", 3)
    retry_delay = task_info.get("retry_delay", 2)
    base_url = task_info.get("base_url")
    api_key = task_info.get("api_key")
    upstream_index = task_info.get("upstream_index")
    skip_existing = task_info.get("skip_existing", False)
    timeout = task_info.get("timeout", 120)
    ref_image = task_info.get("ref_image")  # img2img: local path to reference image
    last_error = None
    file_path = Path(output_dir) / f"{name}.png"

    if skip_existing and file_path.exists():
        safe_print(f"[{index}/{total}] [SKIP] {name} already exists")
        return {"success": True, "name": name, "file": str(file_path), "error": None, "skipped": True}

    for attempt in range(max_retries):
        try:
            mode_label = "[img2img]" if ref_image else "[txt2img]"
            safe_print(f"[{index}/{total}] {mode_label} start: {name} (attempt {attempt + 1}/{max_retries})")
            result = generate_image_single(
                prompt=prompt,
                output_dir=output_dir,
                resolution=resolution,
                filename=name,
                silent=False,  # always log errors even in batch mode
                base_url=base_url,
                api_key=api_key,
                upstream_index=upstream_index,
                timeout=timeout,
                ref_image=ref_image,
            )
            if result:
                safe_print(f"[{index}/{total}] [OK] {name}")
                return {"success": True, "name": name, "file": result, "error": None, "skipped": False}
            safe_print(f"[{index}/{total}] [FAIL] {name}, retrying...")
            last_error = "empty image generation result"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            safe_print(f"[{index}/{total}] [ERROR] {name}: {last_error}")

        if attempt < max_retries - 1:
            time.sleep(retry_delay)

    safe_print(f"[{index}/{total}] [FAILED] {name} exhausted retries")
    return {"success": False, "name": name, "file": None, "error": last_error, "skipped": False}


def generate_from_config(
    config_path: str = "examples/prompt_config.example.json",
    upstream_index: Optional[int] = None,
    upstream_count: Optional[int] = None,
    timeout: Optional[int] = None,
    force_existing: bool = False,
):
    config_path_obj = Path(config_path).expanduser().resolve()
    with config_path_obj.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    total_count = config.get("total_count", 1)
    resolution = normalize_resolution(config.get("resolution", "1024x1024"))
    global_prompt = config.get("global_prompt", "")
    output_dir = resolve_output_dir(config_path_obj, config.get("output_dir"))
    images = config.get("images", [])
    max_workers = min(int(config.get("max_workers", 50)), 50, max(total_count, 1))
    max_retries = config.get("max_retries", 3)
    retry_delay = config.get("retry_delay", 2)
    policy = normalize_policy(config)
    config_timeout = int(config.get("timeout", policy.get("batch_timeout", 180)))

    if upstream_count is None:
        upstream_count = config.get("upstream_count", 1)
    if upstream_index is None:
        upstream_index = config.get("upstream_index", 0)
    if timeout is None:
        timeout = config_timeout

    baseurls, apikeys, env_upstream_count = parse_upstreams()
    effective_upstream_count = max(upstream_count, env_upstream_count)

    safe_print("=== batch image generation ===")
    safe_print(f"config: {config_path_obj}")
    safe_print(f"count: {total_count}")
    safe_print(f"resolution: {resolution}")
    safe_print(f"workers: {max_workers}")
    safe_print(f"retries: {max_retries}")
    safe_print(f"output_dir: {output_dir}")
    safe_print(f"upstream_mode: {'multi' if effective_upstream_count > 1 else 'single'}")
    safe_print(f"upstream_count: {effective_upstream_count}")
    if effective_upstream_count > 1:
        safe_print(f"upstream_index: {upstream_index} (responsible for images where index % {effective_upstream_count} == {upstream_index})")
    safe_print(f"timeout: {timeout}s")
    safe_print("-" * 50)

    output_dir.mkdir(parents=True, exist_ok=True)

    task_base_url = None
    task_api_key = None
    if baseurls and effective_upstream_count > 0:
        idx = upstream_index % len(baseurls)
        task_base_url = baseurls[idx]
        task_api_key = apikeys[idx]

    tasks = []
    lint_errors = []
    img2img_count = 0
    for i, image_config in enumerate(images[:total_count]):
        name = image_config.get("name", f"image_{i + 1}")
        prompt = image_config.get("prompt", "")
        mode = image_config.get("mode", policy.get("default_mode", "generic"))
        lint_errors.extend(lint_prompt(policy, name, prompt, mode))
        full_prompt = build_full_prompt(global_prompt, prompt, policy, mode)

        # --- img2img: detect reference_image in config ---
        # Resolve relative to config file directory, not CWD
        ref_image = image_config.get("reference_image")
        if ref_image:
            ref_path = (config_path_obj.parent / ref_image).expanduser().resolve()
            if ref_path.exists():
                img2img_count += 1
                ref_image = str(ref_path)
            else:
                safe_print(f"[WARN] {name}: reference_image '{ref_image}' not found (resolved: {ref_path}), falling back to txt2img")
                ref_image = None

        tasks.append(
            {
                "index": i + 1,
                "total": total_count,
                "name": name,
                "prompt": full_prompt,
                "output_dir": str(output_dir),
                "resolution": resolution,
                "max_retries": max_retries,
                "retry_delay": retry_delay,
                "base_url": task_base_url,
                "api_key": task_api_key,
                "upstream_index": upstream_index,
                "skip_existing": bool(policy.get("skip_existing_files", True)) and not force_existing,
                "timeout": timeout,
                "ref_image": ref_image,
            }
        )

    if img2img_count > 0:
        safe_print(f"img2img tasks: {img2img_count}/{len(tasks)}")

    if lint_errors and policy.get("fail_on_prompt_risk", True):
        raise SystemExit("Prompt lint failed:\n" + "\n".join(lint_errors))

    if effective_upstream_count > 1:
        tasks = shard_tasks_for_upstream(tasks, upstream_index, effective_upstream_count)
        safe_print(f"After sharding: {len(tasks)} task(s) assigned to upstream {upstream_index}")

    if not tasks:
        safe_print("No tasks assigned to this upstream instance. Exiting cleanly.")
        return []

    safe_print(f"starting {len(tasks)} task(s)...")
    start_time = time.time()
    results: List[Dict] = []
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(generate_image_task, task): task for task in tasks}
        for future in as_completed(future_to_task):
            completed += 1
            try:
                results.append(future.result())
            except Exception as exc:
                task = future_to_task[future]
                safe_print(f"[ERROR] task {task['name']} failed: {exc}")
                results.append({"success": False, "name": task["name"], "file": None, "error": f"{type(exc).__name__}: {exc}", "skipped": False})

            elapsed = time.time() - start_time
            success_count = sum(1 for item in results if item["success"])
            failed_count = sum(1 for item in results if not item["success"])
            safe_print(f"progress {completed}/{len(tasks)} | success {success_count} | failed {failed_count} | elapsed {elapsed:.1f}s")

    total_time = time.time() - start_time
    success_count = sum(1 for item in results if item["success"])
    failed_count = sum(1 for item in results if not item["success"])
    safe_print("=" * 50)
    safe_print("=== done ===")
    safe_print(f"time: {total_time:.2f}s")
    safe_print(f"success: {success_count}/{len(tasks)}")
    safe_print(f"failed: {failed_count}/{len(tasks)}")
    safe_print(f"output_dir: {output_dir}")

    write_generation_report(config_path_obj, output_dir, results, config)

    attempted = [item for item in results if not item.get("skipped")]
    attempted_failed = [item for item in attempted if not item.get("success")]
    if attempted and len(attempted_failed) == len(attempted):
        safe_print("[FATAL] All image generation tasks failed - upstream is likely down.")
        safe_print("Do NOT silently fall back. Fix the upstream API configuration first.")
        raise SystemExit(f"All {len(attempted_failed)} attempted image generation tasks failed. Upstream API may be down.")

    return results


def generate_filename_from_prompt(prompt: str) -> str:
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "show",
        "system",
        "screen",
        "image",
        "interface",
        "page",
        "view",
        "realistic",
        "screenshot",
    }
    chinese_chars = re.findall(r"[\u4e00-\u9fff]+", prompt)
    english_words = re.findall(r"[a-zA-Z]+", prompt)

    keywords = []
    for word in chinese_chars:
        if word not in stop_words and len(word) >= 2:
            keywords.append(word)
    for word in english_words:
        if word.lower() not in stop_words and len(word) >= 2:
            keywords.append(word.lower())

    if not keywords:
        clean_prompt = re.sub(r"[^\w\s]", "", prompt)
        clean_prompt = re.sub(r"\s+", "_", clean_prompt.strip())
        keywords = [clean_prompt[:50]]

    filename = "_".join(keywords[:5])
    filename = re.sub(r"[^\w\-_]", "_", filename)
    filename = re.sub(r"_+", "_", filename).strip("_")
    if len(filename) > 100:
        filename = filename[:100]
    return f"{filename}.png"


def probe_upstream_img2img(base_url: str, api_key: str, ref_image_path: str, timeout: int) -> Tuple[bool, str]:
    """Probe whether an upstream supports img2img via /v1/images/edits (multipart form)."""
    path = Path(ref_image_path).expanduser().resolve()
    if not path.exists():
        return False, f"reference image not found: {ref_image_path}"

    url = f"{base_url.rstrip('/')}/v1/images/edits"
    try:
        with path.open("rb") as fh:
            files = {"image": (path.name, fh, "image/png")}
            data = {
                "prompt": "enhance this image with better lighting and sharpness, keep same content",
                "model": "gpt-image-2",
                "n": "1",
                "size": "1024x1024",
            }
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.post(url, files=files, data=data, headers=headers, timeout=timeout)
            response.raise_for_status()
            result = response.json()
    except requests.exceptions.Timeout:
        return False, f"timeout after {timeout}s"
    except requests.exceptions.ConnectionError as exc:
        return False, f"connection error: {exc}"
    except requests.exceptions.HTTPError as exc:
        return False, f"http error: {exc}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

    data_items = result.get("data") or []
    if not data_items:
        return False, "response has no data items"
    first = data_items[0]
    if first.get("url") or first.get("b64_json"):
        return True, "valid img2img image payload received (edits endpoint)"
    return False, "response data missing url/b64_json"


def check_upstream(upstream_index: int = 0, upstream_count: int = 1, timeout: int = 150, retries: int = 3, probe_img2img: bool = False, ref_image_path: Optional[str] = None):
    baseurls, apikeys, count = parse_upstreams()
    if not baseurls:
        safe_print("[FAIL] No upstream configured in .env")
        return False

    indices = range(min(upstream_count, count)) if upstream_count > 1 else [0]
    any_ok = False
    probe_results = []
    for i in indices:
        if i >= len(baseurls):
            break
        probe_label = "img2img" if probe_img2img else "txt2img"
        safe_print(f"Probing upstream {i} ({probe_label}): {baseurls[i]}")
        upstream_ok = False
        last_error = "empty image generation result"
        for attempt in range(retries):
            if probe_img2img and ref_image_path:
                ok, detail = probe_upstream_img2img(baseurls[i], apikeys[i], ref_image_path, timeout)
            else:
                ok, detail = probe_upstream_once(baseurls[i], apikeys[i], timeout)
            if ok:
                safe_print(f"  [OK] Upstream {i} ({probe_label}) is available (attempt {attempt + 1}/{retries})")
                any_ok = True
                upstream_ok = True
                last_error = detail
                break
            last_error = detail
            safe_print(f"  [WARN] Upstream {i} probe miss (attempt {attempt + 1}/{retries}): {detail}")
        if not upstream_ok:
            safe_print(f"  [DEGRADED] Upstream {i} did not pass probe after {retries} attempts: {last_error}")
        probe_results.append({"upstream": i, "ok": upstream_ok, "last_error": last_error, "mode": probe_label})

    if any_ok and any(not item["ok"] for item in probe_results):
        safe_print("[DEGRADED] At least one upstream is usable. Continuing is allowed; failed upstreams can be bypassed or repaired later.")
    if not any_ok:
        timeout_only = probe_results and all(str(item.get("last_error", "")).startswith("timeout after") for item in probe_results)
        if timeout_only:
            safe_print("[DEGRADED-PASS] All probe misses were timeouts only. This is not strong enough evidence to prove image generation is impossible.")
            safe_print("[DEGRADED-PASS] Allowing the workflow to continue. Use the real generation step as the final judge.")
            return True
        safe_print("[FAIL] No upstream passed probe. This is a real upstream failure.")
    return any_ok


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="GPT Image 2 batch generator for auto-lab (txt2img + img2img).",
        epilog=(
            "Multi-upstream mode:\n"
            "  python generate_images.py --config prompt_config.json --upstreams 3\n"
            "  python generate_images.py --config prompt_config.json --upstream 0\n"
            "  python generate_images.py --config prompt_config.json --upstream 1\n"
            "  python generate_images.py --config prompt_config.json --upstream 2\n"
            "\n"
            "img2img (single-image test):\n"
            "  python generate_images.py --prompt 'enhance this UI' --ref-image screenshot.png\n"
            "\n"
            "img2img (batch with config):\n"
            '  Add "reference_image": "path/to/ref.png" to any image entry in prompt_config.json\n'
        ),
    )
    parser.add_argument("--config", "-c", help="Path to prompt_config.json (default: examples/prompt_config.example.json)")
    parser.add_argument("--check", action="store_true", help="Test upstream API connectivity without generating images")
    parser.add_argument("--prompt", "-p", help="Single test prompt (used with --check or standalone test)")
    parser.add_argument("--ref-image", "-r", help="Path to a reference image for img2img mode (single-image test with --prompt)")
    parser.add_argument("--upstream", "-u", type=int, default=None, help="Specify which upstream to use (0-based index). Use with --upstreams for multi-upstream mode.")
    parser.add_argument("--upstreams", "-U", type=int, default=None, help="Total number of upstreams for sharding. When > 1, tasks are distributed by index modulo upstreams.")
    parser.add_argument("--timeout", "-t", type=int, default=None, help="Request timeout in seconds (default: 180 for multi-upstream, 120 for single).")
    parser.add_argument("--force-existing", action="store_true", help="Regenerate even when the target image file already exists.")
    return parser.parse_args()


def main():
    safe_print("=== GPT Image 2 batch generator ===")
    args = parse_args()

    if args.check:
        config_timeout = args.timeout
        config_retries = None
        if args.config and Path(args.config).exists():
            config_data = json.loads(Path(args.config).read_text(encoding="utf-8"))
            policy = normalize_policy(config_data)
            config_timeout = config_timeout or int(config_data.get("timeout", policy.get("probe_timeout", 150)))
            config_retries = int(policy.get("probe_retries", 3))
        ok = check_upstream(
            upstream_index=args.upstream or 0,
            upstream_count=args.upstreams or 1,
            timeout=config_timeout or 150,
            retries=config_retries or 3,
            probe_img2img=bool(args.ref_image),
            ref_image_path=args.ref_image,
        )
        raise SystemExit(0 if ok else 1)

    if args.prompt:
        safe_print(f"Test prompt: {args.prompt}")
        if args.ref_image:
            safe_print(f"img2img mode: reference image = {args.ref_image}")
        probe_dir = skill_root() / ".probe_cache"
        probe_dir.mkdir(exist_ok=True)
        result = generate_image_single(
            args.prompt,
            output_dir=str(probe_dir),
            ref_image=args.ref_image,
        )
        if result:
            safe_print(f"[SUCCESS] image saved: {result}")
        else:
            safe_print("[FAILED] image generation failed")
        return

    baseurls, _, env_upstream_count = parse_upstreams()
    config_upstream_count = 1

    if args.upstreams is not None:
        config_upstream_count = args.upstreams
    elif env_upstream_count > 1:
        config_upstream_count = env_upstream_count
    elif args.upstream is not None:
        config_upstream_count = max(env_upstream_count, 1)

    if config_upstream_count > 1 and args.upstream is None:
        if env_upstream_count == 1:
            args.upstream = 0
        else:
            safe_print(
                f"Multi-upstream mode detected ({config_upstream_count} upstreams). "
                f"Specify --upstream N to select which upstream to use.\n"
                f"Example: python generate_images.py --config prompt_config.json --upstreams {config_upstream_count} --upstream 0"
            )
            raise SystemExit(1)

    timeout = args.timeout or (180 if config_upstream_count > 1 else 120)

    config_path = args.config
    if not config_path:
        if args.check or args.prompt:
            config_path = str(skill_root() / "examples" / "prompt_config.example.json")
        else:
            raise SystemExit(
                "Batch image generation requires --config <path/to/prompt_config.json>.\n"
                "The config should be in your init_run output directory.\n"
                "Example: python generate_images.py --config output/my_project/prompt_config.json"
            )
    if not Path(config_path).exists():
        default_config = skill_root() / "examples" / "prompt_config.example.json"
        if default_config.exists():
            config_path = str(default_config)
        else:
            safe_print("No config found, and no default example config is available.")
            raise SystemExit(1)

    safe_print(f"Using config file: {config_path}")
    generate_from_config(
        config_path=config_path,
        upstream_index=args.upstream or 0,
        upstream_count=config_upstream_count,
        timeout=timeout,
        force_existing=args.force_existing,
    )


if __name__ == "__main__":
    main()

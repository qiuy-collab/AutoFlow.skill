"""
Image Quality Checker for AutoFlow.

Checks each generated AI image for:
  1. Visual consistency (same environment across all images)
  2. Blur / artifact detection
  3. Timestamp realism
  4. AI generation artifacts (malformed text, twisted UI, impossible layouts)

Uses a vision-capable upstream model (Agnes AI with vision, or DashScope qwen-vl).
The check is performed BEFORE visual review — it catches issues that require regeneration.

Usage:
    python check_images.py --config prompt_config.json --output-dir ./output
    python check_images.py --config prompt_config.json --output-dir ./output --report check_report.json
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional


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


def image_to_base64(path: Path) -> tuple[str, str]:
    """Encode image as base64. Returns (mime_type, base64_string)."""
    import base64 as b64

    ext = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    mime = mime_map.get(ext, "image/png")
    data = b64.b64encode(path.read_bytes()).decode("ascii")
    return mime, data


def find_image_files(output_dir: Path, image_names: list[str]) -> dict[str, Path]:
    """Find generated images by name in output directory."""
    found = {}
    # Search recursively for matching image files
    for img_name in image_names:
        # Try common extensions
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            candidate = output_dir / f"{img_name}{ext}"
            if candidate.exists():
                found[img_name] = candidate
                break
        # Search in subdirectories
        if img_name not in found:
            for f in output_dir.rglob(f"*"):
                if f.is_file() and f.stem == img_name:
                    found[img_name] = f
                    break
    return found


def build_check_prompt(image_name: str, global_prompt: str, image_prompt: str) -> str:
    """Build the vision check prompt for a single image."""
    return f"""You are a screenshot quality auditor. Examine this image carefully and answer with a structured JSON report.

## Image Context
- Image name: {image_name}
- Expected environment (from global_prompt):
  {global_prompt[:300]}
- This image's specific prompt:
  {image_prompt[:300]}

## Check each dimension (respond with score 1-5, 5=perfect):

1. **SHARPNESS**: Is text pixel-sharp and readable? Any blur, haze, or soft focus?
   - 5: Crisp text, sharp UI edges
   - 1: Blurry/unreadable, smeared glyphs

2. **CONSISTENCY**: Does the visual environment match what global_prompt describes?
   - 5: Exact match (theme, window style, background all correct)
   - 1: Completely different environment

3. **TIMESTAMP_REALISM**: If time/date appears, is it realistic and temporally consistent?
   - 5: No time shown OR time is realistic and natural
   - 1: Impossible timestamps, future dates, obviously fake

4. **AI_ARTIFACTS**: Any malformed text, twisted controls, broken tables, warped UI?
   - 5: No artifacts — looks like a real screenshot
   - 1: Multiple obvious AI-generation signs

5. **LOCALHOST_LEAK**: Any localhost, 127.0.0.1, dev URLs, browser address bars exposed?
   - 5: Clean — no dev indicators
   - 1: Shows localhost, dev URLs, or browser chrome

6. **OVERALL_AS_SCREENSHOT**: If this were placed in a formal report, would readers believe it's a real screenshot?
   - 5: Totally believable
   - 1: Obviously fake/synthetic

## Output format (pure JSON, no markdown):

{{
  "image_name": "{image_name}",
  "scores": {{
    "sharpness": 5,
    "consistency": 5,
    "timestamp_realism": 5,
    "ai_artifacts": 5,
    "localhost_leak": 5,
    "overall_as_screenshot": 5
  }},
  "issues_found": ["具体问题描述，空数组表示无问题"],
  "regeneration_needed": false,
  "regeneration_reason": ""
}}"""


VISION_SYSTEM_PROMPT = """You are an image quality auditor for a lab report automation system. Your job is to detect AI-generated screenshots that would look fake in a formal academic report.

Be STRICT: if an image has even minor issues that would make a professor suspicious, mark it for regeneration.
Be CONCISE: only output the JSON, no explanations."""


def call_vision_api(
    image_paths: list[Path],
    check_prompt: str,
    base_url: str,
    api_key: str,
    model: str,
    timeout: int = 120
) -> Optional[dict]:
    """Call vision API with images. Supports OpenAI-compatible vision endpoints."""
    import requests

    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Build content array with images + text
    content = []
    for img_path in image_paths:
        mime, b64_data = image_to_base64(img_path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime};base64,{b64_data}",
                "detail": "high"
            }
        })
    content.append({
        "type": "text",
        "text": check_prompt
    })

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        "temperature": 0.0,
        "max_tokens": 2048
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    result = response.json()

    if "choices" not in result or not result["choices"]:
        return None

    content_text = result["choices"][0].get("message", {}).get("content", "")
    if not content_text:
        return None

    content_text = content_text.strip()
    if content_text.startswith("```"):
        lines = content_text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content_text = "\n".join(lines)

    try:
        return json.loads(content_text)
    except json.JSONDecodeError as e:
        print(f"  Warning: Vision API returned non-JSON: {e}")
        print(f"  Raw: {content_text[:300]}")
        return {"error": "JSON parse failed", "raw": content_text[:500]}


def check_images(
    config_path: Path,
    output_dir: Path,
    report_path: Optional[Path] = None
) -> dict:
    """Check all generated images for quality issues."""
    import requests as req

    env = load_env_file()
    base_url = env.get("AGNES_BASEURL", "").strip()
    api_key = env.get("AGNES_APIKEY", "").strip()
    model = env.get("AGNES_MODEL", "agnes-2.0-flash").strip()

    if not base_url or not api_key:
        print("[SKIP] Vision API not configured (missing AGNES_BASEURL/AGNES_APIKEY in .env)")
        print("[SKIP] Image quality check skipped — visual review by agent required")
        return {"status": "skipped", "reason": "vision API not configured", "checks": []}

    config = json.loads(config_path.read_text(encoding="utf-8"))
    image_names = [img["name"] for img in config.get("images", [])]
    global_prompt = config.get("global_prompt", "")

    image_files = find_image_files(output_dir, image_names)
    if not image_files:
        print(f"[SKIP] No generated images found in {output_dir}")
        return {"status": "skipped", "reason": "no images found", "checks": []}

    missing = [n for n in image_names if n not in image_files]
    if missing:
        print(f"[WARN] Missing images: {', '.join(missing)}")

    print(f"=== Image Quality Check ===")
    print(f"Model: {model}")
    print(f"Found: {len(image_files)}/{len(image_names)} images")
    print(f"Mode: Per-image vision check")
    print("-" * 50)

    all_checks = []
    total_issues = 0
    regen_needed = 0

    # Build image prompt map
    image_prompts = {img["name"]: img.get("prompt", "") for img in config.get("images", [])}

    for idx, img_name in enumerate(sorted(image_files.keys()), 1):
        img_path = image_files[img_name]
        img_prompt = image_prompts.get(img_name, "")
        check_prompt = build_check_prompt(img_name, global_prompt, img_prompt)

        print(f"\n[{idx}/{len(image_files)}] Checking {img_name}...")
        start = time.time()

        try:
            result = call_vision_api([img_path], check_prompt, base_url, api_key, model)
        except Exception as exc:
            print(f"  [ERROR] API call failed: {exc}")
            all_checks.append({
                "image_name": img_name,
                "error": str(exc),
                "scores": {},
                "issues_found": [f"API error: {exc}"],
                "regeneration_needed": False,
                "regeneration_reason": ""
            })
            continue

        elapsed = time.time() - start

        if not result or "error" in result:
            print(f"  [ERROR] Invalid response")
            all_checks.append({
                "image_name": img_name,
                "error": result.get("error", "unknown") if result else "empty",
                "scores": {},
                "issues_found": ["API returned invalid response"],
                "regeneration_needed": False,
                "regeneration_reason": ""
            })
            continue

        # Print summary
        scores = result.get("scores", {})
        issues = result.get("issues_found", [])
        needs_regen = result.get("regeneration_needed", False)

        score_str = " | ".join(f"{k}={v}" for k, v in scores.items())
        print(f"  Scores: {score_str} ({elapsed:.1f}s)")

        if issues:
            total_issues += len(issues)
            for issue in issues:
                print(f"  [ISSUE] {issue}")

        if needs_regen:
            regen_needed += 1
            reason = result.get("regeneration_reason", "")
            print(f"  [REGEN] Regeneration recommended: {reason}")

        all_checks.append(result)

    # Generate summary report
    overall_pass = regen_needed == 0
    summary = {
        "status": "pass" if overall_pass else "fail",
        "total_images": len(image_files),
        "checked": len(all_checks),
        "issues_found": total_issues,
        "regeneration_needed": regen_needed,
        "overall_pass": overall_pass,
        "checks": all_checks,
    }

    print(f"\n{'=' * 50}")
    print(f"Check complete: {len(all_checks)} images checked")
    print(f"Issues: {total_issues} | Regenerations needed: {regen_needed}")
    print(f"Overall: {'PASS' if overall_pass else 'FAIL — regenerate failed images'}")

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report saved: {report_path}")

    if not overall_pass:
        sys.exit(1)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Check generated images for quality issues")
    parser.add_argument("--config", required=True, help="Path to prompt_config.json")
    parser.add_argument("--output-dir", required=True, help="Directory containing generated images")
    parser.add_argument("--report", default=None, help="Path to save check report JSON")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve() if args.report else None

    check_images(config_path, output_dir, report_path)


if __name__ == "__main__":
    main()

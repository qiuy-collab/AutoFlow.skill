"""
Prompt JSON Validator for auto-lab.

Three-layer validation:
  Layer 0 — STRUCTURAL: local-only, checks all required fields exist (no API needed)
  Layer 1 — REQUIREMENT: checks each image matches WORK_PLAN scoring items (needs API + vision)
  Layer 2 — CONSISTENCY: checks prompt semantics, forbidden terms, cross-image consistency (needs API)

Usage:
    # Layer 0 only (fast, local, no API)
    python validate_prompt.py --config prompt_config.json --mode structure

    # Full three-layer validation (needs API)
    python validate_prompt.py --config prompt_config.json --mode full

    # With requirement-gating (Layer 1)
    python validate_prompt.py --config prompt_config.json --mode full --requirements WORK_PLAN.md

    # Auto-fix + output
    python validate_prompt.py --config prompt_config.json --fix --output report.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict

import requests


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_env_file() -> dict:
    """Load .env from skill root."""
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


# ── Layer 0: Structure validation (local, no API) ──────────────────────────

REQUIRED_TOP_KEYS = [
    "total_count", "resolution", "output_dir", "upstream_count", "upstream_index",
    "max_workers", "max_retries", "retry_delay", "timeout",
    "concurrency_source", "concurrency_report", "upstream_mode",
    "image_policy", "global_prompt", "images"
]

REQUIRED_IMAGE_KEYS = ["name", "mode", "prompt"]

REQUIRED_IMAGE_POLICY_KEYS = [
    "default_mode", "auto_append_negative", "fail_on_prompt_risk",
    "probe_retries", "probe_timeout", "batch_timeout", "skip_existing_files",
    "forbidden_terms", "ui_density", "crop_browser_chrome", "forbid_localhost_or_dev_url",
    "quality_constraints"
]

REQUIRED_QUALITY_KEYS = ["consistency", "pixel_sharpness", "no_blur_or_mosaic", "time_consistency"]


def validate_structure(config: dict, config_dir: Path) -> dict:
    """Layer 0: check all required fields exist, values are plausible, reference_image paths valid."""
    checks: List[Dict] = []
    all_pass = True

    # ── top-level keys ──
    for key in REQUIRED_TOP_KEYS:
        if key not in config:
            checks.append({
                "rule": f"Layer 0 — missing top-level key: {key}",
                "result": "fail",
                "issue": f"Required key '{key}' is missing from prompt_config.json",
                "fix_suggestion": f"Add '{key}' field (see TEMPLATE.json for expected format)",
                "affected_field": key
            })
            all_pass = False
        elif key == "total_count" and not isinstance(config[key], int):
            checks.append({
                "rule": f"Layer 0 — invalid type: {key}",
                "result": "fail",
                "issue": f"total_count must be an integer, got {type(config[key]).__name__}",
                "fix_suggestion": "Set total_count to the number of images[] entries",
                "affected_field": "total_count"
            })
            all_pass = False

    for key in REQUIRED_TOP_KEYS:
        if key in config and key not in [c["affected_field"] for c in checks]:
            checks.append({
                "rule": f"Layer 0 — top-level key present: {key}",
                "result": "pass",
                "issue": "",
                "fix_suggestion": "",
                "affected_field": ""
            })

    # ── total_count vs images array length ──
    if "total_count" in config and "images" in config and isinstance(config["total_count"], int):
        actual = len(config["images"])
        expected = config["total_count"]
        if actual != expected:
            checks.append({
                "rule": "Layer 0 — total_count mismatch",
                "result": "fail",
                "issue": f"total_count={expected} but images[] has {actual} entries",
                "fix_suggestion": f"Set total_count to {actual} or add/remove images[] entries to match",
                "affected_field": "total_count"
            })
            all_pass = False
        else:
            checks.append({
                "rule": "Layer 0 — total_count matches images[]",
                "result": "pass",
                "issue": "",
                "fix_suggestion": "",
                "affected_field": ""
            })

    # ── image_policy keys ──
    if "image_policy" in config and isinstance(config["image_policy"], dict):
        policy = config["image_policy"]
        for key in REQUIRED_IMAGE_POLICY_KEYS:
            if key not in policy:
                checks.append({
                    "rule": f"Layer 0 — missing image_policy key: {key}",
                    "result": "fail",
                    "issue": f"Required image_policy key '{key}' is missing",
                    "fix_suggestion": f"Add '{key}' to image_policy (see TEMPLATE.json)",
                    "affected_field": f"image_policy.{key}"
                })
                all_pass = False

        # quality_constraints sub-keys
        if "quality_constraints" in policy and isinstance(policy["quality_constraints"], dict):
            for qk in REQUIRED_QUALITY_KEYS:
                if qk not in policy["quality_constraints"]:
                    checks.append({
                        "rule": f"Layer 0 — missing quality_constraints key: {qk}",
                        "result": "fail",
                        "issue": f"Required quality_constraints key '{qk}' is missing",
                        "fix_suggestion": f"Add '{qk}': true to image_policy.quality_constraints",
                        "affected_field": f"image_policy.quality_constraints.{qk}"
                    })
                    all_pass = False

    # ── per-image keys ──
    if "images" in config and isinstance(config["images"], list):
        for idx, img in enumerate(config["images"]):
            prefix = f"images[{idx}]"
            for key in REQUIRED_IMAGE_KEYS:
                if key not in img:
                    checks.append({
                        "rule": f"Layer 0 — missing image key: {prefix}.{key}",
                        "result": "fail",
                        "issue": f"Required image key '{key}' is missing in {prefix}",
                        "fix_suggestion": f"Add '{key}' to {prefix}",
                        "affected_field": f"{prefix}.{key}"
                    })
                    all_pass = False

            # reference_image is optional, but if present, must be a valid path
            if "reference_image" in img and img["reference_image"]:
                ref_path = Path(img["reference_image"])
                if not ref_path.is_absolute():
                    ref_path = config_dir / ref_path
                if not ref_path.exists():
                    checks.append({
                        "rule": f"Layer 0 — reference_image not found: {prefix}",
                        "result": "fail",
                        "issue": f"reference_image '{img['reference_image']}' does not exist on disk (resolved to {ref_path})",
                        "fix_suggestion": "Verify the reference_image path is correct, or remove the field for txt2img mode",
                        "affected_field": f"{prefix}.reference_image"
                    })
                    all_pass = False
                else:
                    checks.append({
                        "rule": f"Layer 0 — reference_image valid: {prefix}",
                        "result": "pass",
                        "issue": f"reference_image found: {ref_path.name}",
                        "fix_suggestion": "",
                        "affected_field": ""
                    })

            # mode values
            if "mode" in img and img["mode"] not in ("screenshot_strict", "generic"):
                checks.append({
                    "rule": f"Layer 0 — invalid mode: {prefix}",
                    "result": "fail",
                    "issue": f"mode must be 'screenshot_strict' or 'generic', got '{img['mode']}'",
                    "fix_suggestion": "Set mode to 'screenshot_strict' (for UI/terminal) or 'generic' (for other)",
                    "affected_field": f"{prefix}.mode"
                })
                all_pass = False

            # name format
            if "name" in img:
                import re
                if not re.match(r'^img_\d{2,}$', img["name"]):
                    checks.append({
                        "rule": f"Layer 0 — invalid name format: {prefix}",
                        "result": "fail",
                        "issue": f"name must follow 'img_NN' format (e.g. img_01), got '{img['name']}'",
                        "fix_suggestion": "Rename to img_01, img_02, ... with continuous numbers",
                        "affected_field": f"{prefix}.name"
                    })
                    all_pass = False

    # ── mark all remaining keys as pass ──
    unmarked = _find_unmarked_structural_checks(config)
    for um in unmarked:
        checks.append(um)

    return {
        "layer": 0,
        "layer_name": "structural",
        "overall_result": "pass" if all_pass else "fail",
        "summary": f"Structure validation: {'all fields present' if all_pass else 'missing or invalid fields found'}",
        "checks": checks,
        "required_changes": [],
        "auto_fix_applied": False,
        "auto_fix_count": 0
    }


def _find_unmarked_structural_checks(config: dict) -> List[Dict]:
    """Generate pass entries for structural items not yet covered by explicit checks."""
    results = []
    # naming continuity check
    if "images" in config and isinstance(config["images"], list):
        names = [img.get("name", "") for img in config["images"]]
        expected = [f"img_{i+1:02d}" for i in range(len(names))]
        if names != expected:
            results.append({
                "rule": "Layer 0 — naming continuity",
                "result": "fail",
                "issue": f"Image names are not continuous: got {names}, expected {expected}",
                "fix_suggestion": "Rename images to img_01, img_02, ... in order",
                "affected_field": "images[].name"
            })
        else:
            results.append({
                "rule": "Layer 0 — naming continuity",
                "result": "pass",
                "issue": "",
                "fix_suggestion": "",
                "affected_field": ""
            })

    # resolution check
    res = config.get("resolution", "")
    if res not in ("2560x1440", "2048x1152", "1024x1024"):
        results.append({
            "rule": "Layer 0 — resolution validity",
            "result": "warn",
            "issue": f"Unusual resolution: '{res}'. Expected 2048x1152 or 2560x1440 for screenshots.",
            "fix_suggestion": "Set resolution to '2048x1152' (standard 16:9 wide screen)",
            "affected_field": "resolution"
        })
    else:
        results.append({
            "rule": "Layer 0 — resolution validity",
            "result": "pass",
            "issue": "",
            "fix_suggestion": "",
            "affected_field": ""
        })

    return results


# ── Layer 1+2: Requirement & Consistency (needs API) ────────────────────────

def build_validation_prompt(config_json: str, requirements_text: str = "") -> str:
    """Build a comprehensive validation prompt for the Agnes AI validator."""
    req_section = ""
    if requirements_text:
        req_section = f"""
## 需求文档 / WORK_PLAN

以下是本次任务的需求文档内容，用于需求符合性检查：

```
{requirements_text[:4000]}
```
"""

    return f"""你是一个 JSON 提示词校验专家。请对以下 prompt_config.json 执行双重审核。

## 第一重审核：需求符合性 (Layer 1)
{req_section if req_section else "（未提供需求文档，跳过此层）"}

### 规则 R1: 图片与评分项映射
- 如果提供了需求文档/WORK_PLAN，逐张检查 images[] 中的每张图片是否对应了评分标准中的至少一个得分点
- 检查是否有评分项遗漏了对应图片（某个得分点没有任何图片覆盖）
- 检查每张图片的 prompt 描述是否与需求中的功能描述一致

### 规则 R2: 生成方式合理性
- 如果某张图片有 reference_image 字段（img2img 模式），检查其 prompt 是否描述了"期望的修改"（如增强亮度、统一风格）而非从零描述整个场景
- 如果某张图片没有 reference_image（txt2img 模式），检查 prompt 是否完整描述了目标场景
- 混合使用 txt2img 和 img2img 时，检查图片间的视觉一致性是否可维持

## 第二重审核：内部一致性 (Layer 2)

### 规则 C1: global_prompt 与 images[].prompt 语义一致性
- global_prompt 定义了统一的视觉环境（桌面环境、终端主题、窗口风格等）
- 每个 image.prompt 的描述必须与 global_prompt 完全兼容，不能自相矛盾
- 例如：global_prompt 说"深色终端主题"，某个 image 不能说"白色背景"

### 规则 C2: 禁止词检查
- 检查 global_prompt 和每个 image.prompt 是否包含以下禁止词：
  流程图、架构图、讲解板、说明面板、悬浮标注、箭头标注、海报、AI生成、示意图、
  poster、callout、annotation、flowchart、diagram
- 注意：如果在"不要"、"不能有"、"无"、"without"、"avoid"的否定上下文中出现，视为通过

### 规则 C3: mode 字段正确性
- 截图类 prompt 的 mode 必须是 "screenshot_strict"
- 非截图类 prompt 的 mode 可以是 "generic"

### 规则 C4: 图片间视觉一致性
- 如果多张图片声称在"同一环境"中，检查它们的 prompt 是否真的描述了相同环境
- 特别关注：使用 img2img 增强的图片是否保持了与原 txt2img 图片一致的环境风格

### 规则 C5: 分辨率合理性
- "2560x1440" 或 "2048x1152" 适合截图（16:9 宽屏）
- "1024x1024" 适合非截图类

### 规则 C6: image_policy 配置完整性
- forbidden_terms 列表是否完整
- default_mode 是否为 "screenshot_strict"（当所有图片都是截图时）
- fail_on_prompt_risk 是否为 true

### 规则 C7: total_count 与 images 数组长度匹配
- total_count 必须等于 images 数组的长度

### 规则 C8: 图片命名规范
- image.name 必须以 "img_" 开头，编号连续（img_01, img_02...）

## 输出格式要求

你必须严格输出以下 JSON 格式（不要输出 Markdown 代码块，只输出纯 JSON）：

{{
  "overall_result": "pass|fail|warn",
  "summary": "一句话总结校验结果",
  "layers": [
    {{
      "name": "requirement",
      "enabled": true/false,
      "checks": [
        {{
          "rule": "R1: 评分项映射 / R2: 生成方式合理性",
          "result": "pass|fail|warn|skipped",
          "issue": "具体问题描述",
          "fix_suggestion": "修改建议",
          "affected_field": "字段路径"
        }}
      ]
    }},
    {{
      "name": "consistency",
      "checks": [
        {{
          "rule": "C1-C8 中的具体规则名",
          "result": "pass|fail|warn",
          "issue": "具体问题描述",
          "fix_suggestion": "修改建议",
          "affected_field": "字段路径"
        }}
      ]
    }}
  ],
  "required_changes": [
    {{
      "path": "JSON 字段路径",
      "current": "当前值（截取前100字符）",
      "suggested": "建议修改为",
      "reason": "修改原因"
    }}
  ]
}}

## 待校验的 prompt_config.json

```json
{config_json}
```

请严格按照上述规则和输出格式进行校验。只输出纯 JSON，不要输出任何解释文字。"""


VALIDATOR_SYSTEM_PROMPT = """你是一个专业的 JSON 配置校验引擎。你的唯一职责是对输入的 JSON 配置执行规则校验，并输出结构化的校验结果。

严格要求：
1. 只输出纯 JSON，不要包含 Markdown 代码块标记（不要 ```json）
2. 输出必须是可以直接 parse 的有效 JSON
3. 逐条规则检查，不要跳过
4. 对于每一条规则，明确给出 pass/fail/warn
5. required_changes 数组中的每一条必须是具体可执行的修改"""


def call_validator_api(prompt: str, base_url: str, api_key: str, model: str, timeout: int = 120) -> Optional[dict]:
    """Call the Agnes AI validation API."""
    url = f"{base_url.rstrip('/')}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": VALIDATOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 4096
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    result = response.json()

    if "choices" not in result or not result["choices"]:
        return None

    content = result["choices"][0].get("message", {}).get("content", "")
    if not content:
        return None

    # Try to parse the JSON response
    content = content.strip()
    # Remove markdown code block markers if present
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Warning: Validator returned non-JSON response: {e}")
        print(f"Raw response: {content[:500]}")
        return {"error": "JSON parse failed", "raw": content[:1000]}


def validate_config(
    config_path: Path,
    output_path: Optional[Path] = None,
    auto_fix: bool = False,
    mode: str = "full",
    requirements_path: Optional[Path] = None
) -> dict:
    """Validate prompt_config.json."""
    if not config_path.exists():
        raise SystemExit(f"Config file not found: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    config_dir = config_path.parent
    config_json = json.dumps(config, ensure_ascii=False, indent=2)

    print(f"=== Prompt JSON Validation ===")
    print(f"Config: {config_path}")
    print(f"Mode: {mode}")
    print(f"Images: {config.get('total_count', 0)} entries")
    if requirements_path:
        print(f"Requirements: {requirements_path}")
    print("-" * 50)

    # ── Layer 0: always run structure validation first ──
    print("\n[Layer 0] Structure validation (local)...")
    struct_result = validate_structure(config, config_dir)
    struct_checks = struct_result["checks"]
    struct_fails = [c for c in struct_checks if c["result"] == "fail"]
    struct_warns = [c for c in struct_checks if c["result"] == "warn"]

    print(f"  Results: {len([c for c in struct_checks if c['result']=='pass'])} pass, "
          f"{len(struct_fails)} fail, {len(struct_warns)} warn")

    for check in struct_checks:
        status = check["result"]
        if status == "pass":
            continue
        icon = {"fail": "[FAIL]", "warn": "[WARN]"}.get(status, "[????]")
        print(f"  {icon} {check['rule']}: {check.get('issue', '')}")

    # ── If structure-only mode, return early ──
    if mode == "structure":
        result = struct_result
        result["mode"] = "structure"
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\nReport saved: {output_path}")
        return result

    # ── Layer 1+2: need API ──
    env = load_env_file()
    base_url = env.get("AGNES_BASEURL", "").strip()
    api_key = env.get("AGNES_APIKEY", "").strip()
    model = env.get("AGNES_MODEL", "agnes-2.0-flash").strip()

    if not base_url or not api_key:
        raise SystemExit(
            "[ERROR] Agnes AI validator not configured.\n"
            "Add these to .env:\n"
            "  AGNES_BASEURL=https://apihub.agnes-ai.com\n"
            "  AGNES_APIKEY=sk-xxx...\n"
            "  AGNES_MODEL=agnes-2.0-flash"
        )

    print(f"\nValidator: {model} @ {base_url}")
    print(f"Mode: {'auto-fix' if auto_fix else 'report-only'}")

    # Load requirements if provided
    requirements_text = ""
    if requirements_path and requirements_path.exists():
        requirements_text = requirements_path.read_text(encoding="utf-8")
        print(f"\n[Layer 1] Requirement-gated validation (WORK_PLAN loaded: {len(requirements_text)} chars)")
    else:
        print(f"\n[Layer 1] No requirements provided — skipping requirement-gated checks")

    print(f"\n[Layer 2] Consistency validation...")

    validation_prompt = build_validation_prompt(config_json, requirements_text)

    print("Calling validation agent...")
    start_time = time.time()

    max_retries = 2
    result = None
    last_error = None

    for attempt in range(max_retries):
        try:
            result = call_validator_api(validation_prompt, base_url, api_key, model)
            if result and "error" not in result:
                break
            last_error = result.get("error") if result else "empty response"
        except Exception as exc:
            last_error = str(exc)
            print(f"  Attempt {attempt + 1} failed: {last_error}")
            if attempt < max_retries - 1:
                time.sleep(3)

    elapsed = time.time() - start_time

    if not result or "error" in result:
        raise SystemExit(
            f"[FAIL] Prompt validation failed after {max_retries} attempts.\n"
            f"Last error: {last_error}\n"
            f"Time: {elapsed:.1f}s\n"
            f"Check AGNES_BASEURL/AGNES_APIKEY/AGNES_MODEL in .env"
        )

    # Merge Layer 0 results into the final output
    result["layers"] = result.get("layers", [])
    result["layers"].insert(0, {
        "name": "structural",
        "checks": struct_checks
    })

    # Combine verdict
    layer_fails = len(struct_fails) > 0
    for layer in result.get("layers", []):
        if layer["name"] == "structural":
            continue
        for c in layer.get("checks", []):
            if c.get("result") == "fail":
                layer_fails = True

    result["mode"] = "full"
    result["overall_result"] = "fail" if layer_fails else result.get("overall_result", "pass")

    print(f"\nValidation completed in {elapsed:.1f}s")
    print(f"Overall result: {result.get('overall_result', 'unknown')}")
    print(f"Summary: {result.get('summary', 'N/A')}")

    # Print all checks from all layers
    total_pass = total_fail = total_warn = 0
    for layer in result.get("layers", []):
        for check in layer.get("checks", []):
            status = check.get("result", "?")
            icon = {"pass": "[PASS]", "fail": "[FAIL]", "warn": "[WARN]", "skipped": "[SKIP]"}.get(status, "[????]")
            rule = check.get("rule", "Unknown")
            issue = check.get("issue", "")
            if status == "pass":
                total_pass += 1
            elif status == "fail":
                total_fail += 1
                print(f"  {icon} [{layer['name']}] {rule}: {issue}")
            elif status == "warn":
                total_warn += 1
                print(f"  {icon} [{layer['name']}] {rule}: {issue}")

    print(f"\nResults across all layers: {total_pass} pass, {total_fail} fail, {total_warn} warn")
    print("-" * 50)

    # Required changes
    required_changes = result.get("required_changes", [])
    if required_changes:
        print(f"\n=== Required Changes ({len(required_changes)}) ===")
        for i, change in enumerate(required_changes, 1):
            print(f"\n  #{i}: {change.get('path', 'unknown')}")
            print(f"      Reason: {change.get('reason', 'N/A')}")
            current = change.get("current", "")
            suggested = change.get("suggested", "")
            if current:
                print(f"      Current:  {current[:120]}")
            if suggested:
                print(f"      Suggest:  {suggested[:120]}")

    # Auto-fix
    if auto_fix and required_changes:
        print(f"\n=== Auto-fixing prompt_config.json ===")
        fixed_count = 0
        for change in required_changes:
            path_str = change.get("path", "")
            suggested = change.get("suggested", "")
            if not path_str or not suggested:
                continue
            try:
                apply_change(config, path_str, suggested)
                fixed_count += 1
                print(f"  Fixed: {path_str}")
            except Exception as exc:
                print(f"  Failed to fix {path_str}: {exc}")

        if fixed_count > 0:
            backup_path = config_path.with_suffix(".json.bak")
            config_path.rename(backup_path)
            print(f"  Backup: {backup_path}")
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  Written: {config_path} ({fixed_count} changes)")
            print(f"\n  Agent: review the changes and verify before proceeding.")
            result["auto_fix_applied"] = True
            result["auto_fix_count"] = fixed_count
    elif auto_fix:
        print(f"\nNo changes needed — config is clean.")

    # Save report
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReport saved: {output_path}")

    return result


def apply_change(config: dict, path_str: str, suggested: str) -> None:
    """Apply a single change to the config dict using dot/bracket notation path."""
    parts = []
    current = ""
    i = 0
    while i < len(path_str):
        ch = path_str[i]
        if ch == ".":
            if current:
                parts.append(current)
                current = ""
        elif ch == "[":
            if current:
                parts.append(current)
                current = ""
            j = path_str.index("]", i)
            idx = int(path_str[i+1:j])
            parts.append(idx)
            i = j
        else:
            current += ch
        i += 1
    if current:
        parts.append(current)

    target = config
    for part in parts[:-1]:
        if isinstance(part, int):
            target = target[part]
        else:
            target = target[part]

    last = parts[-1]
    if isinstance(last, int):
        target[last] = suggested
    elif last == "prompt" or last == "global_prompt":
        target[last] = suggested
    elif last == "total_count":
        target[last] = int(suggested)
    elif last == "mode":
        target[last] = str(suggested)
    elif last == "resolution":
        target[last] = str(suggested)
    else:
        try:
            target[last] = json.loads(suggested)
        except (json.JSONDecodeError, TypeError):
            target[last] = suggested


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate prompt_config.json — three-layer architecture (structure / requirement / consistency).",
        epilog=(
            "Examples:\n"
            "  # Structure only (fast, no API)\n"
            "  python validate_prompt.py --config prompt_config.json --mode structure\n\n"
            "  # Full validation with requirement-gating\n"
            "  python validate_prompt.py --config prompt_config.json --mode full --requirements WORK_PLAN.md\n\n"
            "  # Full validation + auto-fix + report\n"
            "  python validate_prompt.py --config prompt_config.json --mode full --fix --output report.json"
        )
    )
    parser.add_argument("--config", "-c", required=True, help="Path to prompt_config.json")
    parser.add_argument("--mode", "-m", choices=["structure", "full"], default="full",
                        help="Validation mode: 'structure' (local Layer 0 only) or 'full' (all three layers, needs API)")
    parser.add_argument("--requirements", "-r", help="Path to WORK_PLAN.md or requirements file for Layer 1 requirement-gated checks")
    parser.add_argument("--output", "-o", help="Path to save validation report JSON")
    parser.add_argument("--fix", action="store_true", help="Auto-apply suggested fixes to prompt_config.json (full mode only)")
    parser.add_argument("--timeout", "-t", type=int, default=120, help="API timeout in seconds")
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else None
    requirements_path = Path(args.requirements).expanduser().resolve() if args.requirements else None

    try:
        result = validate_config(
            config_path=config_path,
            output_path=output_path,
            auto_fix=args.fix,
            mode=args.mode,
            requirements_path=requirements_path
        )

        overall = result.get("overall_result", "fail")
        if overall == "fail":
            if args.mode == "structure":
                print("\n[FAIL] Structure validation found missing or invalid fields.")
                print("Fix the above issues in prompt_config.json before proceeding.")
            else:
                print("\n[FAIL] Prompt validation found critical issues.")
                print("Fix the above issues in prompt_config.json before generating images.")
            sys.exit(1)
        elif overall == "warn":
            print("\n[WARN] Prompt validation found warnings. Review before proceeding.")
            sys.exit(0)
        else:
            print("\n[PASS] Prompt validation passed. Ready for image generation.")
            sys.exit(0)

    except SystemExit:
        raise
    except Exception as exc:
        print(f"\n[ERROR] Validation failed: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()

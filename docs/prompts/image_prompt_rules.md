# Image Prompt Rules

This document defines how `auto-lab` should write `prompt_config.json`.

## Scope boundary

`prompt_config.json` is only for the `ai_simulated` route.

Use it for:
- terminal screenshots
- command output screenshots
- software / system configuration screenshots

Do not use it for:
- local frontend page screenshots
- self-built app/web product flows
- development software practice screenshots for the user's own app/web project when the UI should reflect the local running build
- function diagrams, flowcharts, data flow diagrams, or ER diagrams

Those belong to `browser_capture_plan.json` or `diagram_plan.json`.

## Planning order

Before writing prompts:
1. Read the requirement document.
2. Fill `requirement_checklist.json`.
3. If the assignment depends on a pre-task, complete it first and absorb the outputs.
4. Decide whether the run uses `ai_simulated`, `browser_capture`, `diagram_assets`, or a combination.
5. Only write prompts for figures assigned to `ai_simulated`.

## Prompt quality rules

- The goal is believable screenshot realism, not explainer collage style.
- The whole image set should share one coherent environment.
- The whole image set should stay consistent at the environment, lighting, UI rendering, and camera-treatment level.
- Keep the background treatment consistent across the set unless the requirement explicitly needs different scenes.
- Show only necessary information and keep a believable background.
- Avoid high information density, tiny unreadable text blocks, and overloaded dashboards.
- Require pixel-level sharpness, crisp readable text, and clean UI edges.
- Explicitly forbid blur, haze, mosaic blocks, blocky compression, smeared glyphs, and muddy textures.
- If time or date appears on screen, keep it realistic and temporally consistent across the same screenshot session.
- Do not expose `localhost`, `127.0.0.1`, browser address bars, tabs, or dev URLs unless the user explicitly needs them.
- Do not expose AI origin through visible text such as `AI生成`, `示意图`, or similar.
- Do not use poster / callout / diagram language for screenshot prompts.

## Output contract

`prompt_config.json` should:
- match only the `ai_simulated` figures
- keep names aligned with `copywriting.md` placeholders
- never include browser-capture-only or diagram-only figures
- stay free of comments and helper fields

## Resolution and concurrency

- Use `2048x1152` for `2K 16:9`.
- Use `3840x2160` for `4K 16:9`.
- Do not assume maximum concurrency is supported upstream.
- Test 2K/4K 16:9 with `scripts/test_image_concurrency.py` when a batch run will be expensive or time-sensitive.
- If high concurrency fails, reduce to the highest passing worker count and record whether the failure came from upstream API rejection, timeout/rate limits, or a local script/config issue.
- If only part of a batch fails or only a subset needs regeneration after visual review, create and use a supplement config instead of rerunning the full batch.

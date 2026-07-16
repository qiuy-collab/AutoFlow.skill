# Image module

Use this module for visual artifacts. Computation belongs to `task.compute`; this module renders or captures its results.

## Actions

- `capture`: real browser/application/terminal evidence. Prefer deterministic capture from the actual local result.
- `ai`: AI-generated screenshots or explanatory assets only when real capture is unavailable or the request explicitly needs generation.
- `diagram`: architecture, ER, UML, process, data-flow, and other structured diagrams. Prefer deterministic DSL renderers.
- `chart`: plots derived from real task data and calculations.

Read only the route-specific guidance needed:

- AI assets: `docs/prompts/image_prompt_rules.md`, then use `generate_images.py` and `validate_prompt.py`.
- Browser evidence: use `capture_frontend_screenshots.py`; verify the app is real and locally reachable first.
- Diagrams: `docs/prompts/diagram_asset_rules.md`, then use `generate_diagram_assets.py`.
- Quality review: `docs/prompts/visual_review_rules.md` and `check_images.py`.

Group a coherent review batch into one image step. Complete it with the generated directory or manifest as its artifact. A step with `gate_after: visual` activates `VISUAL_STOP`; downstream modules cannot consume the visuals until the user approves them.

Before PLAN_STOP, record every planned visual in `requirement_map.json.planned_figures` with a stable id, requirement ids, route, purpose, and expected caption. The number of generated visuals must satisfy this plan. Do not add decorative figures that prove no requirement.

After generation, preserve the route-specific report, source files for diagrams/charts, real capture URL or command where applicable, and any img2img fixup history. A fix creates a new artifact hash and reopens `VISUAL_STOP`.

Reject blurry text, mosaics, malformed UI, inconsistent scene identity, unreadable diagrams, deceptive screenshots, and charts without labels or data provenance.

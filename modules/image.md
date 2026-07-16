# Image module

Use this module for visual artifacts. Computation belongs to `task.compute`; this module renders or captures its results.

## Actions

- `capture`: real browser/application/terminal evidence. Prefer deterministic capture from the actual local result.
- `ai`: AI-generated screenshots, explanatory assets, and scientific schematics only when real capture is unavailable or the request explicitly needs generation. The scientific-figure adapter uses AutoFlow's `.env` upstream with `gpt-image-2`; it does not call OpenRouter.
- `diagram`: architecture, ER, UML, process, data-flow, and any other structured diagram. Prefer deterministic DSL renderers, but accept arbitrary Mermaid/D2/PlantUML source through the custom DSL route; the built-in semantic kinds are convenience templates, not a closed whitelist.
- `chart`: plots derived from real task data and calculations.

Read only the route-specific guidance needed:

- AI assets: `docs/prompts/image_prompt_rules.md`, then use `generate_images.py` and `validate_prompt.py`.
- Browser evidence: route through AutoFlow's integrated `webapp-testing`
  capability at `integrations/webapp-testing`. Read its `SKILL.md`, run
  `scripts/with_server.py --help` before using the helper, and use
  `capture_frontend_screenshots.py` for the declared capture plan. Verify the
  app is real and locally reachable first.
- Frontend visual quality: when the step declares
  `design_backend: integrated-impeccable`, use the local Impeccable command
  reference and detector via `scripts/impeccable_adapter.mjs`. The adapter is
  offline-only and scans local files; any visual findings become evidence or
  remediation inputs, not an automatic approval.
- Diagrams: `docs/prompts/diagram_asset_rules.md`, then use `generate_diagram_assets.py`.
- Scientific schematics: use `generate_scientific_schematic.py` and validate with `validate_scientific_figure.py`.
- Quality review: `docs/prompts/visual_review_rules.md` and `check_images.py`.

Group a coherent review batch into one image step. Complete it with the generated directory or manifest as its artifact. A step with `gate_after: visual` activates `VISUAL_STOP`; downstream modules cannot consume the visuals until the user approves them.

Before PLAN_STOP, record every planned visual in `requirement_map.json.planned_figures` with a stable id, requirement ids, route, purpose, and expected caption. The number of generated visuals must satisfy this plan. Do not add decorative figures that prove no requirement.

After generation, preserve the route-specific report, source files for diagrams/charts, real capture URL or command where applicable, and any img2img fixup history. A fix creates a new artifact hash and reopens `VISUAL_STOP`.

Reject blurry text, mosaics, malformed UI, inconsistent scene identity, unreadable diagrams, deceptive screenshots, and charts without labels or data provenance.

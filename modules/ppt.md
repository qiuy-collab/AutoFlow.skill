# PPT module

Use this module whenever a `.pptx` file is created or edited.

## Actions

- `create`: create a presentation from the request and approved upstream artifacts.
- `edit`: revise an existing presentation or template.

AutoFlow v3 uses its audited local `presentation-skill` integration for
presentation production:

1. Read `workflow.json.capabilities.ppt.skill_file` and the returned local capability files before touching a presentation.
2. Use `integrations/presentation-skill/scripts/presentation_adapter.py` for `check`, `build`, `qa`, `inventory`, and `extract`.
3. If Node/pptxgenjs or Python/python-pptx is unavailable, stop with a clear `blocked` capability report. Do not silently call a user-level or plugin backend.
4. Never install dependencies or download assets during a deck task; the integration manifest records the exact upstream revision and license.

Consume approved task and image artifacts. Create a slide outline, visual system, and source mapping before generation. Render or thumbnail the deck and inspect every slide for overflow, overlap, clipping, unreadable text, broken media, and visual inconsistency.

PPT steps use `gate_after: visual`. Completing a deck reopens `VISUAL_STOP` even if an earlier image batch was approved, because the assembled slides are a new visual artifact.

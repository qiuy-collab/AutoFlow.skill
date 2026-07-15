# PPT module

Use this module whenever a `.pptx` file is created or edited.

## Actions

- `create`: create a presentation from the request and approved upstream artifacts.
- `edit`: revise an existing presentation or template.

AutoFlow v3 uses an external Skill adapter for presentation production:

1. Locate the installed `pptx` Skill and read its complete `SKILL.md` before touching a presentation.
2. If it is unavailable, try the bundled `presentations` capability exposed by the environment.
3. If neither backend exists, stop at PLAN/INIT with a clear missing-capability report. Do not silently generate a low-quality substitute.
4. Do not copy or vendor proprietary `pptx` Skill files into AutoFlow.

Consume approved task and image artifacts. Create a slide outline, visual system, and source mapping before generation. Render or thumbnail the deck and inspect every slide for overflow, overlap, clipping, unreadable text, broken media, and visual inconsistency.

PPT steps use `gate_after: visual`. Completing a deck reopens `VISUAL_STOP` even if an earlier image batch was approved, because the assembled slides are a new visual artifact.

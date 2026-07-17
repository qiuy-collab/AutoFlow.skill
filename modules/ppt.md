# PPT module

Use this module whenever a `.pptx` file is created or edited.

## Actions

- `create`: create a presentation from the request and approved upstream artifacts.
- `edit`: revise an existing presentation or template.

AutoFlow v3 uses its audited local `presentation-skill` integration for
presentation production:

1. Read `workflow.json.capabilities.ppt.skill_file` and the returned local capability files before touching a presentation.
2. Use `integrations/presentation-skill/scripts/presentation_adapter.py` for `check`, `build`, `qa`, `inventory`, and `extract`.
3. If Node/pptxgenjs or Python/python-pptx is unavailable, run the shared environment provisioner under `.autoflow/runtime/<step-id>/`, retry, and record the probe. Mark the step blocked only after automatic provisioning and fallback installation both fail.
4. Keep installed dependencies in the run runtime directory and do not download unrelated assets. The integration manifest records the exact upstream revision and license.

Consume approved task and image artifacts. Create a slide outline, visual system, and source mapping before generation. Render or thumbnail the deck and inspect every slide for overflow, overlap, clipping, unreadable text, broken media, and visual inconsistency.

For rendering, the adapter prefers LibreOffice when available. On Windows, if
`soffice` is absent but Microsoft PowerPoint is installed, the QA adapter uses
PowerPoint COM automatically and stages normalized `slide-N.png` files in the
QA render directory. Do not fail once for missing LibreOffice and then repeat
the same render manually.

PPT steps use `gate_after: visual`. Completing a deck reopens `VISUAL_STOP` even if an earlier image batch was approved, because the assembled slides are a new visual artifact.

On the Windows PowerPoint fallback, the adapter reuses rendered slides only
when the PPTX hash, adapter fingerprint, expected slide count, and every cached
slide image match. Use `--force-render` only when investigating a render-cache
problem; unchanged decks should not be rendered repeatedly.

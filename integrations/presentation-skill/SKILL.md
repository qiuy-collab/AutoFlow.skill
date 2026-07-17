---
name: presentation-skill
description: "AutoFlow's audited local presentation capability for creating, editing, and verifying editable PowerPoint PPTX files from structured source."
---

# AutoFlow Presentation Skill

This is the curated local route from `siril9/presentation-skill`. It keeps the
upstream skill's core contract while exposing only files that are checked into
this integration and can be verified by AutoFlow.

## Non-negotiable workflow

- Treat `outline.json`, evidence, data, and figure sources as the source of
  truth.
- Build through the checked-in renderer; do not write one-off `python-pptx` or
  `pptxgenjs` scripts in a task workspace.
- Keep text, charts, tables, and shapes editable where practical.
- Run geometry/design QA before delivery and perform rendered visual review
  when the runtime supports it.
- Never install dependencies or call a remote package during a deck task. A
  missing runtime is a `blocked` capability, not permission to improvise.

## Supported local surface

Quick deck generation:

```text
python scripts/presentation_adapter.py build \
  --outline <outline.json> --output <deck.pptx> --style-preset <preset>
```

Strict structural QA:

```text
python scripts/presentation_adapter.py qa \
  --input <deck.pptx> --outdir <qa-dir> --skip-render
```

Inventory and source extraction are available for existing decks. The adapter
reports exact missing dependencies before executing any renderer or QA command.
The renderer needs Node.js plus `pptxgenjs`; strict QA needs Python plus
`python-pptx`; rendered image review additionally needs a working office/PDF
conversion chain.

Read the task-specific references under `references/` rather than loading the
entire upstream corpus. AutoFlow's `VISUAL_STOP` remains authoritative: a PPT
step is not consumable by Word or package until the assembled deck is shown and
approved.

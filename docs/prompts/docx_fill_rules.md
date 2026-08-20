# DOCX Fill Rules

This document defines how `AutoFlow office.fill` (format `word`) should preserve a supplied template shell.

## Core policy

- Preserve the template structure and styling intent.
- Save to a new output file, never overwrite the source template.
- The unified office module drives document work through the `officecli` binary (`scripts/office_engine.py`); never fall back to a user-level Word/Python Skill.
- After editing, run the office acceptance pipeline (`office_engine.py validate` + `validate_office.py`) and keep the engine report as part of `office.validation`.
- Plan figures before writing report text.
- Default target tier is `excellent`.
- Default report style is figure-supported, not pure-text.
- Write from the perspective of a student submitting completed coursework, not from the perspective of an agent describing actions.

## Route boundary

Four image actions may appear in the same document:

- `image.ai`
  - terminal screenshots
  - command output screenshots
  - software/system configuration screenshots

- `image.capture`
  - local frontend page screenshots
  - self-built app/web screenshots
  - development software practice screenshots for the user's own app/web flow

- `image.diagram` / `image.chart`
  - function diagrams
  - flowcharts
  - data flow diagrams
  - ER diagrams

- `video.analyze` / `video.record`
  - existing operation videos
  - short local operation recordings
  - representative frame evidence

## Mandatory pre-work

Before editing the document:
1. Read the template and identify headings, body zones, tables, and figure anchors.
2. Read `.autoflow/config/workflow.json` and `.autoflow/config/artifact_manifest.json`; use only inputs declared for the office step.
3. Confirm all upstream task steps are completed and all consumed artifacts still validate.
4. If the document consumes image or PPT artifacts, confirm `VISUAL_STOP` is approved.
5. Read the relevant module plans under `plans/` rather than assuming every route exists.
7. Combine task outputs with the original request instead of writing a disconnected generic report.
8. Review the template for directories, field-based tables of contents, sample text, formatting instructions, and reference wording that must be replaced or removed.

## Figure rules

- If the template already contains image placeholders, reuse them.
- If not, place figures at planned semantic anchors.
- Each figure should have:
  - a lead-in sentence
  - the image
  - a caption
  - a short analysis paragraph

## Verification expectations

The template-specific verify script should check at least:
- no unresolved placeholders remain unless intentionally documented
- the planned figure count is satisfied
- route coverage is satisfied when multiple routes are required
- declared video analysis/recording artifacts exist when the document consumes video evidence
- filled-reference cleanup preserved cover/front matter and retained level-1/level-2 headings when required
- task artifacts are accurately reflected when the request depends on them
- captions exist
- figures are not dumped at the end without context
- placeholder/sample text is removed
- template formatting instructions and reference wording are removed when they are not part of the final report content
- table-of-contents or directory areas are not silently left broken when the template expects them to be filled or updated
- report narration stays in student voice instead of tool/agent voice
- the template shell remains stable

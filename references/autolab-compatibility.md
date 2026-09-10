# AutoLab compatibility matrix

This matrix prevents the modular AutoFlow architecture from silently dropping proven AutoLab behavior. Read it when changing a module contract, validator, recipe, or run file.

| AutoLab capability | AutoFlow owner | Enforcement |
|---|---|---|
| Environment check and dependency setup | Agent / module backends | [environment initialization](init.md), project manifest inspection, and `task.environment` evidence |
| Requirement and rubric analysis | core | `.autoflow/config/WORK_PLAN.md` plus `.autoflow/config/requirement_map.json` |
| Pre-task detection and execution | task | Explicit DAG step; no convenience-only invented task |
| GitHub project selection | task | `task.research`, `SOURCE_STOP`, `task.build` |
| Figure count and evidence mapping | image + core | `requirement_map.json.planned_figures` |
| AI image generation and prompt validation | image | `validate_prompt.py`, `generate_images.py` |
| Browser evidence | image | `capture_frontend_screenshots.py` and `VISUAL_STOP` |
| DSL diagrams | image | `generate_diagram_assets.py`, source plus rendered asset |
| Image fixup | image | img2img clarity/content repair, then reopen `VISUAL_STOP` |
| Template analysis and preservation | office(word) | `.autoflow/intermediate/plans/office.json`, `validate_office.py` |
| Placeholder and template-instruction removal | office(word) | `validate_office.py` hard checks |
| Student voice | office(word) | automated agent-voice scan plus recorded human/Agent review evidence |
| Figure-caption pairing | office(word) | image/caption/lead-in/analysis checks in `validate_office.py` |
| TOC, sections, tables, headers, footers | office(word) | template comparison in `validate_office.py` |
| Reference document cleanup | office(word) | officecli edits on `office.edit`/`office.fill`, plan contract |
| Video metadata and sampled-frame review | video | `video_process.py analyze` validation report |
| Requirement-driven package | package | `.autoflow/intermediate/plans/package.json`, per-file requirement ids and manifest checks |
| Final requirement acceptance | core | `delivery_review.json` and `DELIVERY_STOP` |
| Human plan/image/delivery confirmation | core | PLAN, VISUAL, DELIVERY STOP gates |
| Durable recovery | core | workflow, state, manifest, hashes, gate history |

## Intentional changes

- AutoFlow does not recreate the monolithic `run_workflow.py run` command. Module work remains independently visible and resumable.
- `pre_task_plan.json` is replaced by explicit task steps in the DAG.
- `approval_checkpoints.json` is replaced by gate history in `run_state.json`.
- A fixed `submit.zip` is no longer assumed unless the request requires it; package contents remain requirement-driven.
- Legacy AutoLab workflow files remain incompatible and must be reinitialized.

## Change rule

A capability may move to a different module or contract, but it must not disappear without an explicit decision recorded in this matrix and covered by a regression test.

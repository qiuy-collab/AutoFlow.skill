# Acceptance contracts

Read this reference when preparing PLAN_STOP or DELIVERY_STOP, or when a run includes Word, video, images, or packaging.

## Requirement map

`requirement_map.json` is required before PLAN_STOP approval. Every required item contains:

- a stable id and source;
- a concrete description and acceptance criteria;
- one or more declared evidence artifact ids;
- a validation status;
- optional scoring weight and notes.

`planned_figures` maps each planned visual to known requirement ids and one image route: `capture`, `ai`, `diagram`, or `chart`.

Before DELIVERY_STOP approval, set the map status to `verified` and every required validation status to `passed`. The core verifies that mapped evidence exists in `.autoflow/config/artifact_manifest.json`.

## Office plan and report

Write `.autoflow/intermediate/plans/office.json` using schema `autoflow/office-plan/1.0`. For template-based coursework, enable preservation, caption pairing, student voice, and rendered review. Run the officecli engine checks first:

```bash
python scripts/office_engine.py validate \
  --document <output.docx> --format word \
  --template <template.docx> --source <source.docx> \
  --report <run>/.autoflow/intermediate/artifacts/office_engine_validation.json
```

Then run:

```bash
python scripts/validate_office.py \
  --document <output.docx> --format word \
  --template <template.docx> \
  --plan <run>/.autoflow/intermediate/plans/office.json \
  --engine-report <run>/.autoflow/intermediate/artifacts/office_engine_validation.json \
  --report <run>/.autoflow/intermediate/artifacts/office_validation.json
```

The same two commands cover `.pptx` (`--format ppt`) and `.xlsx` (`--format excel`).
Register both `office.document` and `office.validation`. The core rejects an
office step if the report is failed, incomplete, stale, or refers to a different
file hash.

For complex Word reports and theses, the plan should also set
`require_title=true`, `minimum_heading_count` to the expected heading count,
and `require_toc=true`. `minimaxdocx`/`minimax-docx` may author the document;
`officecli` remains the common validator and renderer. A plain-text line named
目录 or a stale `Update field to see table of contents` message is not a valid
TOC.

## Video report

Run `video_process.py analyze` after recording, creating, or processing a video. Its output uses `autoflow/video-validation/1.0` and records duration, dimensions, codec, SHA-256, sampled frames, and checks. Do not accept a video with zero duration, unknown dimensions, unknown codec, or failed requested frame sampling.

## Package manifest

Every `include_paths` item in `.autoflow/intermediate/plans/package.json` must include `requirement_ids`. `submit/` holds only final deliverable content; `package_submission.py` refuses secret, VCS, cache, key, Office temporary paths, compiled build output (`dist/`, `build/`, `target/`, `out/`, `bin/`, `obj/`, `.next/`, `*.exe`, `*.dll`, `*.class`, …), editor/tool metadata (`.idea/`, `.vscode/`, `coverage/`), and AutoFlow run metadata (`manifest.json`, `*_manifest.json`, `workflow.json`, `artifact_manifest.json`, `run_state.json`, `requirement_map.json`, `delivery_review.json`). Its manifest uses `autoflow/package-manifest/1.0`, is written to `.autoflow/intermediate/plans/` as run metadata, and records hashes, archive names, requirement mappings, and folder/archive equality. `validate_package_acceptance` requires the bundle, zip, and folder below `submit/`; the manifest itself is exempt and lives outside `submit/`.

Run project/source verification before assembly in `.autoflow/intermediate/verification/`. After assembly, run `package_submission.py --verify-only`; this read-only check must confirm manifest/folder hashes, folder/archive equality, ZIP integrity, and zero forbidden files in both the folder and the archive. Any write inside `submit/` invalidates delivery and requires a package revision.

## Delivery review

Before DELIVERY_STOP approval, fill `delivery_review.json` using schema `autoflow/delivery-review/1.0`:

- exactly one result for every required requirement;
- exactly one result for every registered artifact;
- `present=true` and `correct=true` for each result;
- evidence artifact ids that exist in the manifest;
- no unresolved issues;
- `review_completed=true` and `overall_pass=true`.

The delivery gate validates this file instead of accepting a narrative claim that the work is complete.

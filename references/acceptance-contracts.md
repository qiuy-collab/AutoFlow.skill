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

## Word plan and report

Write `.autoflow/intermediate/plans/word.json` using schema `autoflow/word-plan/1.0`. For template-based coursework, enable preservation, caption pairing, student voice, and rendered review. Run the integrated OpenXML core first:

```bash
python scripts/word_engine.py validate \
  --document <output.docx> \
  --template <template.docx> \
  --report <run>/.autoflow/intermediate/artifacts/word_core_validation.json
```

Then run:

```bash
python scripts/validate_word.py \
  --document <output.docx> \
  --template <template.docx> \
  --plan <run>/.autoflow/intermediate/plans/word.json \
  --core-report <run>/.autoflow/intermediate/artifacts/word_core_validation.json \
  --report <run>/.autoflow/intermediate/artifacts/word_validation.json
```

Register both `word.document` and `word.validation`. The core rejects a Word step if the report is failed, incomplete, stale, or refers to a different document hash.

## Video report

Run `video_process.py analyze` after recording, creating, or processing a video. Its output uses `autoflow/video-validation/1.0` and records duration, dimensions, codec, SHA-256, sampled frames, and checks. Do not accept a video with zero duration, unknown dimensions, unknown codec, or failed requested frame sampling.

## Package manifest

Every `include_paths` item in `.autoflow/intermediate/plans/package.json` must include `requirement_ids`. `package_submission.py` refuses known secret, VCS, cache, key, and Office temporary paths. Its manifest uses `autoflow/package-manifest/1.0` and records hashes, archive names, requirement mappings, and folder/archive equality.

Run project/source verification before assembly in `.autoflow/intermediate/verification/`. After assembly, run `package_submission.py --verify-only`; this read-only check must confirm manifest/folder hashes, folder/archive equality, ZIP integrity, and zero forbidden files. Any write inside `submit/` invalidates delivery and requires a package revision.

## Delivery review

Before DELIVERY_STOP approval, fill `delivery_review.json` using schema `autoflow/delivery-review/1.0`:

- exactly one result for every required requirement;
- exactly one result for every registered artifact;
- `present=true` and `correct=true` for each result;
- evidence artifact ids that exist in the manifest;
- no unresolved issues;
- `review_completed=true` and `overall_pass=true`.

The delivery gate validates this file instead of accepting a narrative claim that the work is complete.

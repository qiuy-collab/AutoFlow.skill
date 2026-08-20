# Submission Package Rules

Use this when the assignment requires a final hand-in archive.

## Core rule

- Packaging is prompt-driven.
- Read the assignment requirement first.
- Decide the exact deliverables from the prompt and `.autoflow/config/artifact_manifest.json`, then write `.autoflow/intermediate/plans/package.json`.
- Derive the archive name from the request; use `submit.zip` only when no name is specified and an archive is required.
- Before delivery, list every required deliverable and review them one by one for correctness, completeness, and presentation quality.

## Output format

- Publish every final artifact below `<run>/submit/`.
- When an archive is required, produce both an inspectable delivery subfolder and its archive below `<run>/submit/`.
- Treat published files as frozen; changes require a package revision.

## Naming rules

- Use the exact archive name required by the source document.
- Do NOT add extra suffixes like "AI版", "完整版", "final", "v2", or any other labels.
- If the source document specifies a different name, use that name in `.autoflow/intermediate/plans/package.json`.
- When no naming is specified and an archive is required, use `submit.zip`.

## Typical packaging decisions

- If the prompt says to submit only the final report, include only the final `.docx`.
- If the prompt says to submit the report plus evidence, include the final `.docx` and the required screenshots, logs, datasets, or videos.
- If the prompt says to submit code or project files, include only the required project folders/files, not the whole workspace by default.

## Exclusions

The authoritative forbidden list lives in `modules/package.md` (compiled
programs, build output, editor/tool metadata, AutoFlow run metadata, and
any other hard rejections enforced by `package_submission.py`). These
rules complement it:

- Do not include temporary files, lock files, editor leftovers, or logs unless the prompt explicitly requires them.
- Do not include duplicate intermediate outputs when the prompt only asks for the final deliverables.
- Do not guess broad packaging scopes such as "zip the whole folder" unless the prompt actually says that.

## Acceptance standard

- Do not treat "file exists" as sufficient acceptance.
- Check whether each packaged deliverable actually matches the requirement wording.
- If code/project files are required, confirm the packaged contents include the real implementation, not only screenshots or a report about it.
- If the assignment names screenshots, data, logs, diagrams, videos, or source code, verify their count, relevance, and quality before packaging.

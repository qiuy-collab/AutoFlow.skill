# Submission Package Rules

Use this when the assignment requires a final hand-in archive.

## Core rule

- Packaging is prompt-driven.
- Read the assignment requirement first.
- Decide the exact deliverables from the prompt and `artifact_manifest.json`, then write `plans/package.json`.
- The final archive name must be `submit.zip` unless the user explicitly requires a different name.
- Before delivery, list every required deliverable and review them one by one for correctness, completeness, and presentation quality.

## Output format

- Produce BOTH a `submit/` folder AND a `submit.zip` in the output directory.
- The `submit/` folder allows easy inspection and modification before final delivery.
- The `submit.zip` is the archive for hand-in.

## Naming rules

- The archive must be named `submit.zip`.
- Do NOT add extra suffixes like "AI版", "完整版", "final", "v2", or any other labels.
- If the source document specifies a different name, use that name in `plans/package.json`.
- When no naming is specified in the source document, always use `submit.zip`.

## Typical packaging decisions

- If the prompt says to submit only the final report, include only the final `.docx`.
- If the prompt says to submit the report plus evidence, include the final `.docx` and the required screenshots, logs, datasets, or videos.
- If the prompt says to submit code or project files, include only the required project folders/files, not the whole workspace by default.

## Exclusions

- Do not include temporary files, lock files, editor leftovers, or logs unless the prompt explicitly requires them.
- Do not include duplicate intermediate outputs when the prompt only asks for the final deliverables.
- Do not guess broad packaging scopes such as "zip the whole folder" unless the prompt actually says that.

## Acceptance standard

- Do not treat "file exists" as sufficient acceptance.
- Check whether each packaged deliverable actually matches the requirement wording.
- If code/project files are required, confirm the packaged contents include the real implementation, not only screenshots or a report about it.
- If the assignment names screenshots, data, logs, diagrams, videos, or source code, verify their count, relevance, and quality before packaging.

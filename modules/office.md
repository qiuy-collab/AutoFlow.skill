# Office module (unified)

Use this module whenever a `.docx`, `.pptx`, or `.xlsx` file is created, edited, or filled.
It is the single entry point for all Office document work and dispatches to a format
submodule below.

## Actions

- `create`: create a new document/workbook/deck without an existing template.
- `edit`: revise an existing file while preserving unrelated content and structure.
- `fill`: fill a supplied template without rebuilding its shell.

Every office step must declare `format` in `{word, ppt, excel}`. Read the dispatched
submodule before acting:

| format | Read | Purpose |
|--------|------|---------|
| word  | `modules/office/word.md`  | DOCX creation, editing, template filling |
| ppt   | `modules/office/ppt.md`   | PPTX creation/editing with visual review |
| excel | `modules/office/excel.md` | XLSX workbooks, formulas, tables, styling |

## Backend

All Office work runs through the `officecli` binary (single dependency, no Office
installation required). AutoFlow drives it via `scripts/office_engine.py` and validates
outputs with `scripts/validate_office.py`; it does not silently call another backend.
If `officecli` is missing, report a blocked capability and stop. Read
`workflow.json.capabilities.office` for the detected exe/version.

The official operating manual is `integrations/officecli/SKILL.md` (checked-in
package copy) — read it before working; the sections below only distill the
constraints that prevent costly mistakes and do not replace the official
documentation.

The module accepts the original request plus any approved task and image artifacts.
It must not consume images while `VISUAL_STOP` is pending or rejected. Read
`references/acceptance-contracts.md` and write `.autoflow/intermediate/plans/office.json`
before editing.

## officecli key constraints

- **Layers**: L1 read/inspect → L2 DOM edit → L3 raw XML. Prefer higher layers; add
  `--json` for structured output.
- **Help is the schema**: before guessing property names or value formats, run
  `officecli help <format> <element>` (or `--json` for machine-readable schema).
  One help query beats guess-fail-retry loops.
- **Addressing**: paths are 1-based XPath-style (`/body/p[3]`, `/slide[1]`,
  `/Sheet1/A1`); prefer stable-ID paths (`/body/p[@paraId=...]`,
  `/slide[N]/shape[@id=...]`) in multi-step edits — positional indices shift on insert.
- **Resident mode**: officecli keeps files in memory and auto-flushes. Only run
  `officecli save` / `officecli close` before a non-officecli program reads the file
  (Word, Excel, renderers, delivery).
- **Atomic batches**: use `officecli batch --json` for multi-step edits; any failed
  item rolls back the whole batch unless `--best-effort` is deliberate.
- **Verify after every file change**: run `officecli validate <file>` and
  `officecli view <file> issues --json`; fix findings before proceeding.

## Validation contract

Run the engine checks first, then the full plan-aware validation:

```bash
python scripts/office_engine.py validate \
  --document <output> --format <word|ppt|excel> \
  --template <template> --source <source> \
  --report <run>/.autoflow/intermediate/artifacts/office_engine_validation.json

python scripts/validate_office.py \
  --document <output> --format <word|ppt|excel> \
  --template <template> --plan <run>/.autoflow/intermediate/plans/office.json \
  --engine-report <run>/.autoflow/intermediate/artifacts/office_engine_validation.json \
  --report <run>/.autoflow/intermediate/artifacts/office_validation.json
```

Register both `office.document` and `office.validation`. The core rejects an office
step if the report is failed, incomplete, stale, or refers to a different file hash
(`office_acceptance` validator). The engine report is reused only when document,
template, source, and validator fingerprints all match; use `--force` only for
cache diagnosis.

After the file is final, render it (e.g. `officecli view <file> html` or the
submodule's render step) and record a passed rendered visual review in the plan
before completing the step.

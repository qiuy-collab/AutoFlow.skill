# Office Backend Selection

AutoFlow keeps one acceptance contract while allowing different authoring
backends. The selected backend is reported by `python scripts/autoflow.py
capabilities --json` and must be available before a managed PLAN_STOP.

## Selection

Set the client-neutral Skill-root `.env` field:

```text
OFFICE_WORD_BACKEND=officecli
```

Allowed values:

- `officecli`: simple Word edits, inspection, validation, and rendering. This
  is the compatibility default.
- `minimaxdocx`: complex Word fill/create/edit work, especially reports and
  theses with heading styles, TOC, captions, and page layout.
- `minimax-docx`: accepted alias for the same optional Minimax Word backend.

`excel` and `ppt` use `officecli`. `officecli` remains the common Word
validation and rendering backend after a Minimax authoring step.

## Optional Minimax Runtime

When `OFFICE_WORD_BACKEND` is `minimaxdocx` or `minimax-docx`, configure one of:

```text
MINIMAX_DOCX_ROOT=<installed minimax docx package or skill root>
MINIMAX_DOCX_COMMAND=<installed minimaxdocx command>
```

The agent must resolve the path from the active client environment or the
package's installer instructions. Do not hard-code a Codex-only directory and
do not silently substitute `officecli` when the selected backend is missing.

## Word Acceptance

Regardless of authoring backend, every Word step must produce:

- `office.document`;
- `office.validation` from the AutoFlow Office validator;
- a real title and heading hierarchy for reports/theses;
- a generated or updateable TOC when the document requires one;
- figure lead-in, caption, and analysis paragraphs;
- a rendered visual review with no overflow, placeholder, or broken media.

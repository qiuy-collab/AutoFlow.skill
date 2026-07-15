# Word module

Use this module whenever a `.docx` file is created, edited, or filled.

## Actions

- `create`: create a new document without an existing template.
- `edit`: revise an existing document while preserving unrelated content and structure.
- `fill`: fill a supplied template without rebuilding its shell.

Read the complete Word backend Skill recorded in `workflow.json.capabilities.word.skill_file` before editing. Prefer `minimax-docx`; use the environment's `documents` Skill when that is the selected backend. The local `vendor/minimax-docx` path is an optional cache, not a portability assumption. Use lightweight Python inspection only when it is enough or when the preferred backend cannot complete the operation.

The module accepts the original request plus any approved task and image artifacts. It must not consume images while `VISUAL_STOP` is pending or rejected.

For template fills:

1. Inspect paragraphs, tables, headers, footers, section settings, placeholders, and embedded media.
2. Identify exact fill locations; do not guess from nearby labels.
3. Preserve fixed text, styles, numbering, page setup, and template structure.
4. Insert approved evidence with captions and explanatory text.
5. Verify no placeholders, template instructions, broken relationships, or unintended duplicate content remain.

For new documents, choose a coherent format appropriate to the audience rather than copying a lab-report layout by default.

Register the final `.docx` as the declared Word artifact only after structural and visual verification.

# Word module

Use this module whenever a `.docx` file is created, edited, or filled.

## Actions

- `create`: create a new document without an existing template.
- `edit`: revise an existing document while preserving unrelated content and structure.
- `fill`: fill a supplied template without rebuilding its shell.

Read the complete Word backend Skill recorded in `workflow.json.capabilities.word.skill_file` before editing. Prefer `minimax-docx`; use the environment's `documents` Skill when that is the selected backend. The local `vendor/minimax-docx` path is an optional cache, not a portability assumption. Use lightweight Python inspection only when it is enough or when the preferred backend cannot complete the operation.

The module accepts the original request plus any approved task and image artifacts. It must not consume images while `VISUAL_STOP` is pending or rejected. Read `references/acceptance-contracts.md` and write `plans/word.json` before editing.

For template fills:

1. Inspect paragraphs, tables, headers, footers, section settings, placeholders, and embedded media.
2. Identify exact fill locations; do not guess from nearby labels.
3. Preserve fixed text, styles, numbering, page setup, and template structure.
4. Insert approved evidence with captions and explanatory text.
5. Verify no placeholders, template instructions, broken relationships, or unintended duplicate content remain.

For a filled reference document that must become a blank reusable template, use `prepare_blank_template.py` under the `word.edit` action and retain its cleanup report.

For new documents, choose a coherent format appropriate to the audience rather than copying a lab-report layout by default.

For coursework/report templates, normally enable these Word-plan checks:

- original output path differs from the template;
- section settings, table shapes, headers, and footers are preserved;
- TOC is retained when the template contains one;
- unresolved placeholders, template instructions, and Agent/AI voice are absent;
- every body figure has one nearby caption, an introductory sentence, and an analysis paragraph;
- caption numbers are unique;
- minimum image count matches `requirement_map.json.planned_figures`;
- student voice and rendered-document review have recorded evidence.

Run `validate_word.py` after the DOCX is final. Register the final `.docx` as `word.document` and the passed report as `word.validation`. AutoFlow compares the report hash with the document and rejects stale or failed reports.

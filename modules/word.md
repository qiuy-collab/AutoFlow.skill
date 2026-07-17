# Word module

Use this module whenever a `.docx` file is created, edited, or filled.

## Actions

- `create`: create a new document without an existing template.
- `edit`: revise an existing document while preserving unrelated content and structure.
- `fill`: fill a supplied template without rebuilding its shell.

Read the complete integrated Word backend Skill recorded in `workflow.json.capabilities.word.skill_file` before editing. AutoFlow routes Word work to `integrations/minimax-docx` through `scripts/word_engine.py`; it does not silently call an external Word Skill. If the .NET runtime or the core source is unavailable, report a blocked capability and stop.

The module accepts the original request plus any approved task and image artifacts. It must not consume images while `VISUAL_STOP` is pending or rejected. Read `references/acceptance-contracts.md` and write `.autoflow/intermediate/plans/word.json` before editing.

For template fills:

1. Inspect paragraphs, tables, headers, footers, section settings, placeholders, and embedded media.
2. Identify exact fill locations; do not guess from nearby labels.
3. Preserve fixed text, styles, numbering, page setup, and template structure.
4. Insert approved evidence with captions and explanatory text.
5. Verify no placeholders, template instructions, broken relationships, or unintended duplicate content remain.

For a filled reference document that must become a blank reusable template, use `prepare_blank_template.py` under the `word.edit` action and retain its cleanup report.

For new documents, choose a coherent format appropriate to the audience rather than copying a lab-report layout by default.

The current integrated `create --content-json` contract is a flat array of
`heading`, `paragraph`, and `pagebreak` items. Tables, lists, and images require
a subsequent edit/assembly phase and final count verification. Never pass the
object-shaped `sections` example used by older upstream documentation.

When using `edit insert-paragraph --style`, supply an existing paragraph style
ID or name. Character styles and unknown IDs are hard errors; do not rely on
Word's silent fallback to Normal.

For coursework/report templates, normally enable these Word-plan checks:

- original output path differs from the template;
- section settings, table shapes, headers, and footers are preserved;
- TOC is retained when the template contains one;
- unresolved placeholders, template instructions, and Agent/AI voice are absent;
- every body figure has one nearby caption, an introductory sentence, and an analysis paragraph;
- caption numbers are unique;
- minimum image count matches `requirement_map.json.planned_figures`;
- student voice and rendered-document review have recorded evidence.

Run `word_engine.py validate` first for the integrated OpenXML checks. When the
bundled subset XSD does not cover legal DrawingML or modern template extension
attributes, the engine retries `fix-order` on an isolated copy and records the
documented `business-plus-preview-required-fallback` mode. This mode is not an
XSD pass: `validate_word.py --core-report ...` must still include a passed
rendered visual review after the DOCX is final. Register the final `.docx` as
`word.document` and the passed report as `word.validation`. AutoFlow compares
both reports' hashes with the document and rejects stale or failed reports.

The core validator reuses a passed report only when document, template,
source, and validator fingerprints all match. Use `--force` only for cache
diagnosis or when validation policy changed without changing those inputs.

# Office submodule: word (.docx)

Dispatched from `modules/office.md` when `format=word`. Select the authoring
backend from `OFFICE_WORD_BACKEND` before editing:

- `minimaxdocx` or `minimax-docx`: preferred for complex report/thesis create,
  template fill, heading hierarchy, TOC, captions, and page layout.
- `officecli`: suitable for simple Word edits and remains the common inspect,
  validate, and render backend.

Validation always follows `scripts/office_engine.py` +
`scripts/validate_office.py`, regardless of the authoring backend.
Read `references/office-backends.md` for the selection contract and runtime
configuration before routing a complex Word artifact.
Read the official operating manual in `integrations/officecli/SKILL.md` first —
this submodule applies it to DOCX workflows, it does not replace it.

## Workflow (per action)

1. Inspect the document with `officecli view <file> outline|stats|text --json` and
   `officecli get <file> <path> --depth N` for structure. For template fills, inspect
   paragraphs, tables, headers, footers, section settings, placeholders, and embedded
   media; identify exact fill locations — do not guess from nearby labels.
2. If the selected backend is `minimaxdocx`/`minimax-docx`, use its local
   package instructions for authoring, then flush the document before handing
   it to officecli. If the selected backend is `officecli`, edit with L2 DOM
   operations:
   - `officecli add <file> <parent> --type paragraph --prop text=... --prop style=<id>`
     — supply an existing paragraph style ID/name; character styles and unknown IDs
     are hard errors (officecli does not silently fall back to Normal).
   - `officecli set <file> <path> --prop ...` for formatting; `--find X --prop ...`
     formats or replaces matched text; `/` scopes the whole document.
   - `officecli batch` for multi-step edits (atomic by default).
   - L3 `raw-set` only when L2 cannot express the change.
3. Preserve fixed text, styles, numbering, page setup, and template structure on fill.
4. Insert approved evidence with captions and explanatory text.
5. Verify with `officecli validate` + `officecli view <file> issues --json`; then run
   the plan-aware validation below and fix every failure.

## Word-specific plan checks (coursework/report templates)

- output path differs from the template;
- section settings, table shapes, headers, and footers are preserved;
- TOC is retained when the template contains one;
- a report or thesis has a real title, heading styles, and a generated or
  updateable TOC rather than plain-text labels;
- unresolved placeholders, template instructions, and Agent/AI voice are absent;
- every body figure has one nearby caption, an introductory sentence, and an analysis
  paragraph; caption numbers are unique;
- minimum image count matches `requirement_map.json.planned_figures`;
- student voice and rendered-document review have recorded evidence.

For a filled reference document that must become a blank reusable template, build the
blank from the template directly with `officecli` edits (remove/clear body content,
keep the shell), then verify no placeholders or template instructions remain.

For new documents, choose a coherent format appropriate to the audience rather than
copying a lab-report layout by default.

## Render review

Render the final document (`officecli view <file> html --browser`, or open the static
HTML) and inspect every page for overflow, overlap, unreadable text, broken media,
and visual inconsistency. Record the review in `.autoflow/intermediate/plans/office.json`
(`visual_review.status=passed` with evidence) — the `rendered_document_review` check
fails without it.

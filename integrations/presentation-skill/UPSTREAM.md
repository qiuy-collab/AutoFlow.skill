# Upstream record

- Source: https://github.com/siril9/presentation-skill
- Revision: `3a22eed290fa2205a1e2de5549b4429c5fffd0`
- Version: `0.9.0`
- License: MIT; see `LICENSE`
- Curated on: 2026-07-17

AutoFlow copies the source-first skill contract, the PptxGenJS renderer, the
editable slide templates, and the geometry/design/visual QA entrypoints. The
large style corpus, showcase decks, plugin hooks, `node_modules`, and bootstrap
scripts are intentionally excluded. They are not needed for the deterministic
AutoFlow route and must not be treated as locally available capabilities.

The integration does not modify upstream source files. `SKILL.md` is the
AutoFlow wrapper; `UPSTREAM_SKILL.md` and `UPSTREAM_DESIGN.md` preserve the
audited upstream guidance for comparison.

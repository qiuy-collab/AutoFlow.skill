# AutoFlow integrations

This directory contains capabilities that AutoFlow has deliberately integrated
and audited from external Skills or projects. It is not a runtime cache.

## Layout

- `minimax-docx/`: the MIT-licensed OpenXML/DOCX kernel, its CLI, XSD rules,
  samples, and scenario guidance. `scripts/word_engine.py` is the only
  AutoFlow entry point for this integration.
- `nature-figure/`: Apache-2.0 provenance and adaptation notes for the
  scientific-figure validator and backend. Image generation itself stays in
  AutoFlow's `scripts/` and uses the configured `.env` upstream.
- `webapp-testing/`: Apache-2.0 Playwright skill for local webapp
  reconnaissance, server lifecycle, browser logs, and screenshot evidence.
- `superpowers/`: MIT-licensed, file-only engineering methodology subset for
  brainstorming, planning, TDD, debugging, review, verification, execution,
  and delivery handoff. Its plugin bootstrap and telemetry are not copied.

Optional capabilities such as `pptx`, `baseline-ui`, and `frontend-design` are
resolved from user-level Skills or plugins. AutoFlow does not copy their
proprietary files into this repository. The integrated `webapp-testing` route
is self-contained and is not resolved from an external Skill at runtime.

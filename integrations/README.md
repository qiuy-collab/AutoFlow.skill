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

Optional capabilities such as `pptx`, `baseline-ui`, `frontend-design`, and
`webapp-testing` are resolved from user-level Skills or plugins. AutoFlow does
not copy their proprietary files into this repository.

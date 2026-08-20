# AutoFlow integrations

This directory contains capabilities that AutoFlow has deliberately integrated
and audited from external Skills or projects. It is not a runtime cache.

Run `python scripts/autoflow.py integrations --json` to audit the complete
catalog. Every integration carries a manifest with its upstream revision,
license, local Skill/reference files, and adapter paths.

## Layout

- `nature-figure/`: Apache-2.0 provenance and adaptation notes for the
  scientific-figure validator and backend. Image generation itself stays in
  AutoFlow's `scripts/` and uses the configured `.env` upstream.
- `impeccable/`: Apache-2.0 frontend design language, command references, and
  local anti-pattern detector. AutoFlow disables its update check and exposes
  only the local adapter.

Office document processing (DOCX/PPTX/XLSX) is handled by the unified office
module backed by `officecli` (scripts/office_engine.py + scripts/validate_office.py).
It is not a checked-in integration directory — the binary is installed from
https://d.officecli.ai and requires no backend integration manifest.

User-level Skills and plugins are not runtime dependencies of the integrated
routes. If a local integration or its declared runtime is unavailable, the
corresponding capability is reported as `blocked`; AutoFlow never treats an
unverified external package as available.

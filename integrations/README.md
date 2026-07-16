# AutoFlow integrations

This directory contains capabilities that AutoFlow has deliberately integrated
and audited from external Skills or projects. It is not a runtime cache.

Run `python scripts/autoflow.py integrations --json` to audit the complete
catalog. Every integration carries a manifest with its upstream revision,
license, local Skill/reference files, and adapter paths.

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
- `impeccable/`: Apache-2.0 frontend design language, command references, and
  local anti-pattern detector. AutoFlow disables its update check and exposes
  only the local adapter.
- `engineering-quality/`: MIT-licensed engineering quality subset from
  `addyosmani/agent-skills`: five-axis code review, security hardening,
  performance optimization, ADR/spec/source guidance, incremental delivery,
  and shipping checks. It is exposed
  through `scripts/engineering_quality_adapter.py` and never installs the
  upstream plugin runtime.
- `agent-skills/`: MIT-licensed curated overlay from the same upstream, adding
  interface design, planning, context engineering, frontend architecture,
  browser DevTools verification, observability, migration, simplification,
  CI/CD, and delivery workflows. It is file-only and routed by
  `scripts/autoflow.py`; overlapping Skills remain in their existing canonical
  integration directories.

Optional capabilities such as `pptx`, `baseline-ui`, and `frontend-design` are
resolved from user-level Skills or plugins. AutoFlow does not copy their
proprietary files into this repository. The integrated `webapp-testing` route
is self-contained and is not resolved from an external Skill at runtime.

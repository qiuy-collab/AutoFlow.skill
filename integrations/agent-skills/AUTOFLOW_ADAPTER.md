# AutoFlow adapter contract

This integration is file-only. `scripts/autoflow_core.py` resolves the local
`SKILL.md` for each selected route and records the absolute path in the CLI
route payload. No network request, package installation, plugin hook, or
external Skill lookup is performed after initialization.

The integration is intentionally a curated overlay. AutoFlow keeps the
existing `engineering-quality` and `superpowers` paths for overlapping Skills,
and uses this directory for the additional planning, interface, frontend,
debugging, observability, delivery, and context workflows.

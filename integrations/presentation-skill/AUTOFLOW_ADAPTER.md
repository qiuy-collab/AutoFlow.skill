# AutoFlow adapter

The local presentation integration is deliberately source-first and offline.
`scripts/presentation_adapter.py` is the only execution entrypoint exposed to
AutoFlow. It supports `check`, `build`, `qa`, `inventory`, and `extract`.

The adapter never runs `npm install`, downloads assets, resolves a remote URL,
or silently falls back to a user-level PPT Skill. `check` returns a machine-
readable capability report with the exact missing executable/module. The core
CLI uses that report to mark PPT work `blocked` until the environment is ready.

The copied renderer and QA scripts remain under this integration so route output
is reproducible and auditable. `package.json` records the upstream dependency
contract but no `node_modules` or bootstrap runtime is committed.

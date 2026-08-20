# AutoFlow directory layout

AutoFlow separates routing instructions, deterministic execution code,
integrated capabilities, and generated run data.

```text
autoflow/
├── SKILL.md                 # compact entrypoint and routing rules
├── modules/                 # task/image/office/video/package contracts (office dispatches by format)
├── integrations/            # audited local capability implementations
├── scripts/                 # CLI, adapters, validators, and executors
├── references/              # workflow contracts, gates, acceptance rules
├── recipes/                 # reusable DAG templates
├── examples/                # schema and plan examples
├── tests/                   # unit and integration tests
├── docs/                    # project documentation site
└── evals/                   # skill evaluation prompts
```

Each user run remains outside the Skill source tree. A run is anchored to the
task project directory — the request file's directory — not the session
workspace root, so runs land inside the task project even when the workspace
root is a parent directory. Pass `--output-dir` to place a run elsewhere:

```text
<task-project>/autoflow/
├── .autoflow/
│   ├── scripts/
│   ├── runtime/
│   ├── intermediate/
│   │   ├── plans/
│   │   ├── artifacts/
│   │   └── verification/
│   └── config/
└── submit/
```

## Integration policy

`integrations/` is the only place for an external Skill or tool that AutoFlow
has reviewed and made locally callable. Each integration carries its
upstream/license record and exposes an AutoFlow adapter when its upstream
entrypoint is not deterministic.

Current integrated capability families include `nature-figure` and
`impeccable`. Office document work is not an integration: it runs through the
external `officecli` binary detected by `scripts/office_engine.py`.

User-level Skills and plugins may be detected as optional adapters, but
AutoFlow never treats an uninstalled or unverified external package as
available.

Read `references/integration-contract.md` before adding or updating an
integration. All checked-in integrations must satisfy its self-containment
fields; partial provenance-only entries are not routable.

## Runtime data

- `.autoflow/config/` stores workflow, mutable state, approvals, request copy,
  requirement map, and path map.
- `.autoflow/intermediate/` stores plans, evidence, logs, and validation reports
  that are not final deliverables.
- `.autoflow/intermediate/verification/` stores isolated test copies, temporary
  databases, migration state, and smoke-test output. Verification must not run
  inside `submit/`.
- `.autoflow/runtime/` stores managed environments and dependency caches made by
  `environment_setup.py`. It must remain outside every registered source
  artifact.
- `.autoflow/scripts/` stores scripts specific to one run; shared executors stay
  in this Skill's `scripts/` directory.
- `submit/` contains only frozen final deliverables intended for handoff.

Disposable backend/test directories such as `test_output/`, `output/`,
`generated_images/`, `conversations/`, and `.probe_cache/` are not source,
examples, or deliverables. Never commit runtime artifacts, credentials, caches,
or temporary browser profiles to the Skill package.

# AutoFlow directory layout

AutoFlow is the active Skill. Its repository is deliberately split by
responsibility so routing instructions, deterministic execution code,
integrated capabilities, and generated run data do not get mixed together.

```text
autoflow/
├── SKILL.md                 # compact entrypoint and routing rules
├── modules/                 # task/image/word/ppt/video/package contracts
├── integrations/            # audited, local capability implementations
├── scripts/                 # CLI, adapters, validators, and executors
├── references/              # workflow contracts, gates, acceptance rules
├── recipes/                 # reusable DAG templates
├── examples/                # schema and plan examples
├── tests/                   # standard-library and integration smoke tests
├── docs/                    # project documentation site
└── evals/                   # skill evaluation prompts
```

## Integration policy

`integrations/` is the only place for an external Skill or tool that AutoFlow
has deliberately reviewed and made locally callable. Each integration should
carry its upstream/license record and expose an AutoFlow adapter when its
upstream entrypoint is not already deterministic.

There is intentionally no `vendor/` directory. The old AutoLab vendor layout
was retired after its useful capabilities were moved to `integrations/` or
replaced by a local adapter. User-level Skills and plugins may still be
detected as optional adapters, but AutoFlow never treats an uninstalled or
unverified external package as available.

## Runtime data

Workflow runs belong under `task_runs/` and generated outputs belong under
`output/`, `generated_images/`, `conversations/`, or `test_output/`. These are
runtime artifacts and remain ignored by Git; they are not part of the Skill
package or its directory contract.

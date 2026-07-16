# AutoFlow adapter contract

This integration supplies engineering-quality guidance to the local route
resolver. It is intentionally file-only: no package installation, plugin
bootstrap, remote update, or network call is performed at runtime.

| AutoFlow step | Local guidance | Route meaning |
|---|---|---|
| `task.build` / `task.execute` | code review, security, ADRs | review the implementation across correctness, architecture, security, and maintainability before downstream artifacts consume it |
| `task.compute` | performance optimization | measure the real bottleneck, then optimize and re-measure |
| `package.assemble` | shipping and launch, ADRs | prepare a reversible, verifiable delivery handoff and record important decisions |
| `task.research` | spec-driven and source-driven development | turn the request into a concrete specification and ground framework decisions in authoritative documentation before implementation |
| multi-file task changes | incremental implementation | land thin, verified slices instead of one untestable batch |

The deterministic entrypoint is:

```bash
python scripts/engineering_quality_adapter.py check --json
python scripts/engineering_quality_adapter.py route --module task --action build --json
```

The adapter resolves only files under
`integrations/engineering-quality`. If any required file is missing, it
reports `missing` and AutoFlow blocks the affected plan instead of silently
falling back to an external copy.

# Environment contract

Use this contract for `task.build` and any execution step that depends on a
project runtime. Environment preparation is Agent-driven: read
[environment initialization](init.md),
inspect the actual project manifest and entry points, then run only the needed
installation and verification commands. Do not invoke an environment setup or
auto-detection script.

Keep environments below `<run>/.autoflow/runtime/<step-id>/`, never inside
`project.source`. When `task.environment` is declared, the Agent writes a
factual `autoflow/environment-report/1.0` JSON report with this minimum shape:

```json
{
  "$schema": "autoflow/environment-report/1.0",
  "command": "agent-init",
  "project": "<absolute project.source path>",
  "runtime_root": "<absolute runtime path outside project.source>",
  "status": "ready",
  "missing_tools": [],
  "checks": [{"name": "<actual verification command>", "status": "passed"}]
}
```

Complete the step only when the report is ready, no tools are missing, and
every recorded verification check passed. A step may become `blocked` only for
credentials, paid licensing, an unavoidable reboot, or denied administrative
access after the Agent's attempted commands are recorded.

Do not package `.autoflow/runtime`, `.venv`, `venv`, `node_modules`, package-manager caches, or generated runtime databases. Package lock files and startup scripts instead.

## Isolation and verification

Run destructive or write-producing verification in `<run>/.autoflow/intermediate/verification/<step-id>/` or in the original intermediate project, never in `submit/`. After final packaging, allow only `package_submission.py --verify-only` against the published delivery.

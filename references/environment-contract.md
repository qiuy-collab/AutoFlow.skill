# Environment contract

Use this contract for `task.build` and any execution step that depends on a project runtime.

## Required sequence

1. Detect project ecosystems from manifests and entry points.
2. Run `environment_setup.py ensure`; do not report an ordinary missing runtime or dependency to the user.
3. Keep environments below `<run>/.autoflow/runtime/<step-id>/`, never inside `project.source`.
4. Register the resulting `autoflow/environment-report/1.0` file as `task.environment` when declared.
5. Complete the step only when the report status is `ready`, no tools are missing, and every verification check passed.

```powershell
python scripts/environment_setup.py ensure `
  --project <project.source> `
  --runtime-root <run>/.autoflow/runtime/build `
  --report <run>/.autoflow/intermediate/artifacts/environment_report.json
```

The provisioner tries the existing runtime first, then the platform package manager and a secondary package manager where available. A step may become `blocked` only for credentials, paid licensing, an unavoidable reboot, or denied administrative access after automatic attempts are recorded.

Do not package `.autoflow/runtime`, `.venv`, `venv`, `node_modules`, package-manager caches, or generated runtime databases. Package lock files and startup scripts instead.

## Isolation and verification

Run destructive or write-producing verification in `<run>/.autoflow/intermediate/verification/<step-id>/` or in the original intermediate project, never in `submit/`. After final packaging, allow only `package_submission.py --verify-only` against the published delivery.

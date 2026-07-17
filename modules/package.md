# Package module

Use this module to assemble the final delivery from explicitly declared artifacts.

## Action

- `assemble`: create an inspectable delivery folder, archive when requested, and machine-readable manifest.

Derive package contents and naming from the user request. Do not zip the entire workspace by habit. Include only declared artifacts plus required runtime files, documentation, or source dependencies.

Write `.autoflow/intermediate/plans/package.json` with `source_root`, `include_paths`, `exclude_globs`, output names, and `requirement_ids` for every included path. Final deliverables must be written below `submit/`. Run all source/application verification first in `.autoflow/intermediate/verification/`; never execute tests, migrations, installers, or applications in `submit/`.

Run `package_submission.py --config .autoflow/intermediate/plans/package.json` exactly once after inputs are frozen. It assembles in an isolated staging directory, recursively excludes VCS/runtime/cache/secret paths, validates the folder and archive, then atomically publishes the result. After publication run only:

```bash
python scripts/package_submission.py --config <package.json> --verify-only
```

Retain the `autoflow/package-manifest/1.0` manifest. It must show matching folder/archive listings, per-file hashes, requirement mappings, exclusion counts, ZIP integrity, and no sensitive files.

At PLAN_STOP, run `package_submission.py --config .autoflow/intermediate/plans/package.json --validate-plan`. This checks path containment and requirement mappings without requiring source artifacts that downstream steps have not produced yet.

Reject missing files, duplicate archive paths, symbolic links, secrets, caches, temporary outputs, nested copies of the package itself, and names that violate the request. If an input changes after packaging, revise the package step instead of testing or patching the published folder.

The route for `package.assemble` also includes the local engineering-quality
shipping checklist and ADR guidance. Use them to make the handoff reproducible,
reversible where applicable, and explicit about what was verified.

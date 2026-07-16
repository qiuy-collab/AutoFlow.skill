# Package module

Use this module to assemble the final delivery from explicitly declared artifacts.

## Action

- `assemble`: create an inspectable delivery folder, archive when requested, and machine-readable manifest.

Derive package contents and naming from the user request. Do not zip the entire workspace by habit. Include only declared artifacts plus required runtime files, documentation, or source dependencies.

Write `plans/package.json` with `source_root`, `include_paths`, `exclude_globs`, output names, and `requirement_ids` for every included path. Run `package_submission.py --config plans/package.json`, inspect the generated folder and archive listing, and retain the `autoflow/package-manifest/1.0` manifest. It must show matching folder/archive listings, per-file hashes, requirement mappings, and no sensitive files.

At PLAN_STOP, run `package_submission.py --config plans/package.json --validate-plan`. This checks path containment and requirement mappings without requiring source artifacts that downstream steps have not produced yet.

Reject missing files, duplicate archive paths, secrets, caches, temporary outputs, nested copies of the package itself, and names that violate the request.

# Package module

Use this module to assemble the final delivery from explicitly declared artifacts.

## Action

- `assemble`: create an inspectable delivery folder, archive when requested, and machine-readable manifest.

Derive package contents and naming from the user request. Do not zip the entire workspace by habit. Include only declared artifacts plus required runtime files, documentation, or source dependencies.

Write `plans/package.json` with `source_root`, `include_paths`, `exclude_globs`, output names, and the requirement each item satisfies. Run `package_submission.py --config plans/package.json`, inspect the generated folder and archive listing, and register the requested package artifact.

Reject missing files, duplicate archive paths, secrets, caches, temporary outputs, nested copies of the package itself, and names that violate the request.

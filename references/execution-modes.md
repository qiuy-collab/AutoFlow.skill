# AutoFlow execution modes

Choose the mode before creating any run files. Naming AutoFlow in the request selects this Skill; it does not by itself select managed mode.

## Direct mode

Direct mode is the default for a small request when all conditions below hold:

1. Exactly one module is needed.
2. The result is one semantic artifact family.
3. No artifact depends on another module's output.
4. No GitHub candidate choice, package contract, rubric-wide evidence mapping, resumable state, or consequential external action is required.
5. The scope is clear and low-risk.

Multiple representations of the same artifact are one family. For example, Mermaid source plus SVG and PNG exports are one diagram, not three workflow deliverables.

Direct mode uses [environment initialization](init.md) only for environment preparation. It must initialize
the task workspace with `.autoflow/intermediate`, `.autoflow/runtime`, and
`submit/`, then resolve the local route. It does not select a recipe or create
`.autoflow/config/workflow.json`, `WORK_PLAN.md`, `requirement_map.json`,
`artifact_manifest.json`, `delivery_review.json`, or approval gates:

```bash
python scripts/autoflow.py direct-route --module image --action diagram --json
```

Then read the returned module/capability files, perform the task, validate the output, and report the artifact path below `submit/`. Generate the minimum output set that satisfies the request. If the user did not ask for editable source, multiple export formats, a manifest, or a validation report, do not present those as extra deliverables; keep renderer-required temporary files ephemeral where practical. Direct mode has no PLAN, SOURCE, VISUAL, or DELIVERY STOP. A preview requested by the user is feedback, not a workflow approval gate.

Examples:

- Generate one ER diagram and export editable source plus SVG/PNG.
- Create one chart from already supplied data.
- Resize or inspect one video.
- Make a focused edit to one existing Word document when no broader evidence workflow is involved.
- Create one standalone image from an unambiguous prompt.

## Managed mode

Managed mode is required when any direct condition fails. Typical signals:

- Two or more modules or dependent artifact families.
- A project/source-code build that needs GitHub-first discovery and candidate selection.
- A final submission directory, ZIP, package manifest, or requirement-driven delivery contract.
- A complex template/rubric whose requirements must map to evidence across sections or artifacts.
- Work that must be resumed, revised, audited, or handed to another Agent.
- Significant destructive, public, financial, security-sensitive, or otherwise consequential actions.
- A large single deliverable whose structure requires a material user decision before production.

Managed mode initializes the durable run, uses the DAG, and enforces only the STOP gates that apply to the managed recipe.

## Tie-breakers

- Do not use file count as a proxy for workflow complexity. Sidecars and export formats can belong to one artifact family.
- Do not create a plan merely to justify work that is already clear.
- Do not remove useful validation in direct mode; remove orchestration overhead, not quality checks.
- Validation may run internally without producing a user-facing report file unless the request or module acceptance genuinely needs one.
- If one missing choice blocks direct execution, ask one focused question. Do not initialize a managed run unless the answer changes dependencies, scope, safety, or acceptance.
- If the request starts direct but expands into dependent modules or a package, explain the change and initialize managed mode before doing the newly expanded work.

# AutoFlow workflow contract

## Durable files

- `workflow.json` is the declarative DAG. It changes only when the user approves a revised plan.
- `run_state.json` is mutable execution state for steps and STOP gates.
- `artifact_manifest.json` records verified outputs and their hashes.
- `requirement_map.json` maps requirements and scoring items to declared evidence.
- `delivery_review.json` records final correctness for every requirement and artifact.
- `WORK_PLAN.md` is the human-readable plan reviewed at `PLAN_STOP`.
- `plans/` contains module-specific plans such as `source_candidates.json` and `package.json`.
- `workflow.json.capabilities` records the integrated methodology and backend
  paths resolved during initialization; route decisions must use those paths.

## Workflow step

Every step contains:

```json
{
  "id": "word",
  "module": "word",
  "action": "fill",
  "needs": ["task", "image"],
  "inputs": ["request", "task.result", "image.assets"],
  "outputs": ["word.document"],
  "validator": "artifacts_exist",
  "optional": false,
  "gate_after": "visual"
}
```

`needs` controls execution order. `inputs` and `outputs` are artifact IDs. `request` is the only built-in input. Output IDs must be unique across the workflow.

When the Agent changes a custom DAG before PLAN_STOP, run `autoflow.py sync --workflow ...`. Synchronization is rejected after any step has started.

Allowed modules and actions:

- task: research, build, compute, execute
- image: capture, ai, diagram, chart
- word: create, edit, fill
- ppt: create, edit
- video: analyze, record, create, process
- package: assemble

Word steps use `word_acceptance` with `word.document` and `word.validation`. Video steps use `video_acceptance` with `video.media` and `video.validation`. Package steps use `package_acceptance` with `package.bundle` and `package.manifest`. Other steps use `artifacts_exist` unless their module contract defines a stricter report validator.

## State transitions

Steps start as `pending` and become `ready` after their dependencies complete and no STOP blocks execution.

- pending/ready → running
- running → blocked/completed/failed
- blocked/failed → running
- optional pending/ready → skipped

A completed or skipped step is terminal. To redo it, revise the workflow/run rather than editing state by hand.

Complete a step with one `--artifact ID=PATH` for every declared output. AutoFlow verifies existence, records consumers, calculates SHA-256, and rejects undeclared or missing outputs.

## Agent-led execution

AutoFlow does not contain a generic `run` command. The Agent reads the relevant module file, performs the work with the appropriate tool or Skill, and uses the CLI only to validate and advance state. This keeps human choices and cross-Skill operations visible while preserving deterministic gates and artifact contracts.

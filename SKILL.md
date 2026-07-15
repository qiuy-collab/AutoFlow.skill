---
name: autoflow
description: "Orchestrate multi-step artifact workflows by composing task, image, Word, PowerPoint, video, and packaging modules with durable state and mandatory human STOP gates. Use this skill whenever the user explicitly asks for autoflow, and also for substantial work that must produce multiple connected artifacts such as a runnable project plus screenshots and documentation, a report plus slides, or a complete submission package. Do not use it for simple questions or isolated one-step edits unless the user explicitly invokes autoflow."
---

# AutoFlow

AutoFlow turns a request into an explicit artifact DAG. The Agent plans and performs module work; deterministic scripts validate dependencies, state transitions, approvals, and outputs.

Explicit invocation always wins: if the user asks for `autoflow`, use this workflow even for an unusual module combination.

## Core principles

- Compose only the modules the request needs: `task`, `image`, `word`, `ppt`, `video`, `package`.
- Preserve decisions and evidence in files so another Agent can resume the run.
- Treat `workflow.json` as a contract, not a narrative checklist.
- Complete real prerequisite work before writing downstream documents about it.
- Never infer approval from silence. Respect PLAN, SOURCE, VISUAL, and DELIVERY STOP gates.
- Register only real, validated artifacts. Placeholder code, mock evidence, and unverified deliverables do not count.
- This is AutoFlow Schema 1.0. Do not run legacy AutoLab workflow files.

## Read before acting

Always read:

1. `references/workflow-contract.md`
2. `references/stop-gates.md`

Then read only the modules selected for this run:

| Module | Read | Purpose |
|---|---|---|
| task | `modules/task.md` | Research, GitHub-first builds, computation, execution |
| image | `modules/image.md` | Capture, AI assets, diagrams, charts |
| word | `modules/word.md` | DOCX creation, editing, template filling |
| ppt | `modules/ppt.md` | PPTX creation/editing through the external pptx adapter |
| video | `modules/video.md` | Analysis, recording, creation, processing |
| package | `modules/package.md` | Requirement-driven delivery assembly |

## Start a run

1. Inspect the request and all supplied files before asking discoverable questions.
2. Choose the closest recipe:
   - `lab-report`: task → image → word → package
   - `report-and-slides`: task → image → word + ppt → package
   - `project-delivery`: GitHub discovery → build → image → package
   - `document`: optional task/image → word
   - `presentation`: optional task/image → ppt
   - `custom`: Agent-authored DAG
3. Put the durable user request in a UTF-8 file. Do not rely on conversation memory alone.
4. Initialize:

```bash
python scripts/autoflow.py init \
  --request-file <request.md> \
  --output-dir <run-directory> \
  --recipe <recipe-or-auto>
```

5. Read the generated `workflow.json`, `run_state.json`, `artifact_manifest.json`, and `WORK_PLAN.md`.
6. If `auto` produced the neutral `custom` recipe, replace its steps with the actual DAG before asking for approval.
7. Fill every `WORK_PLAN.md` section with the goal, workflow, outputs, scope, constraints, STOP points, and validation strategy.
8. After editing workflow steps, synchronize the still-unstarted state and validate the configuration:

```bash
python scripts/autoflow.py sync --workflow <run-directory>/workflow.json
python scripts/autoflow.py validate --workflow <run-directory>/workflow.json
```

9. Show the plan to the user and stop. After explicit approval, record it:

```bash
python scripts/autoflow.py approve \
  --workflow <run-directory>/workflow.json \
  --gate plan \
  --note "<summary of the user's explicit approval>"
```

Do not start module work before PLAN_STOP approval.

## Execute the DAG

Ask AutoFlow which steps are ready:

```bash
python scripts/autoflow.py next --workflow <workflow.json>
```

For each ready step:

1. Read its module instructions.
2. Mark it running.
3. Perform the actual work.
4. Validate every declared output.
5. Complete it with exactly one artifact mapping for each declared output.

```bash
python scripts/autoflow.py transition \
  --workflow <workflow.json> \
  --step <step-id> \
  --to running

python scripts/autoflow.py transition \
  --workflow <workflow.json> \
  --step <step-id> \
  --to completed \
  --artifact artifact.id=<absolute-path>
```

Use `--to blocked` when external input is genuinely required and `--to failed --note ...` when execution fails. Only optional steps may be skipped.

AutoFlow has no generic `run` command. The Agent invokes each module's real backend and uses the core CLI for state and validation.

## GitHub-first source selection

Code and runnable project tasks use separate `task.research` and `task.build` steps. Follow `modules/task.md` exactly.

- Search and inspect GitHub before implementation.
- Write `plans/source_candidates.json` with real queries, scores, licenses, revisions, and judgments.
- Completing discovery activates SOURCE_STOP when usable candidates exist.
- Show 3–5 candidates and wait for the user's selection.
- Record the selected candidate and revision before approving the gate.
- Clone and modify only after approval.
- If none are suitable, record rejected candidates and the reason for `from_scratch`; do not create a fake choice.

```bash
python scripts/autoflow.py approve \
  --workflow <workflow.json> \
  --gate source \
  --note "User selected candidate <rank/name>"
```

## Visual review

Any step with `gate_after: visual` activates VISUAL_STOP after completion. Show the actual new artifacts, not only filenames. Downstream Word, PPT, and packaging steps remain blocked until explicit approval.

```bash
python scripts/autoflow.py approve \
  --workflow <workflow.json> \
  --gate visual \
  --note "User approved the displayed visual batch"
```

A later PPT or image batch reopens the same gate because it has not been reviewed yet.

## Delivery review

When all steps complete, AutoFlow activates DELIVERY_STOP. Before asking for approval:

- Run `validate` and resolve every error.
- Show final artifact paths and what requirement each satisfies.
- Inspect Word/PPT/media visually where applicable.
- List archive contents rather than assuming packaging succeeded.
- Confirm source code or applications actually run.

After the user signs off:

```bash
python scripts/autoflow.py approve \
  --workflow <workflow.json> \
  --gate delivery \
  --note "User approved the final delivery"
```

The run is complete only when `run_state.json.status` is `completed`.

## Status and recovery

```bash
python scripts/autoflow.py status --workflow <workflow.json>
python scripts/autoflow.py validate --workflow <workflow.json>
```

- Never hand-edit `run_state.json` or `artifact_manifest.json` to bypass a gate.
- If the user rejects a STOP, record it with `autoflow.py gate --to rejected`, revise the affected plan/artifact, and create a new run when terminal steps must be redone.
- If an artifact changes after registration, validation fails because its hash no longer matches. Re-run the producing step in a revised run.
- If a required external Skill such as `pptx` is missing, stop with a capability report rather than silently substituting a lower-quality backend.

## Definition of done

- The selected recipe or custom DAG matches the request.
- Required STOP approvals are recorded from explicit user responses.
- Every completed step has all declared artifacts.
- Artifact paths exist and hashes validate.
- Module-specific quality checks pass.
- `autoflow.py validate` returns `valid`.
- DELIVERY_STOP is explicitly approved.

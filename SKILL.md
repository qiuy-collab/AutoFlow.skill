---
name: autoflow
description: "Route artifact work through either a lightweight direct module or a managed multi-step workflow. Use direct mode for small single-module deliverables without dependencies or consequential choices; use managed task/image/Word/PowerPoint/video/package DAGs with durable state and human STOP reviews for connected or high-consequence work. Explicit autoflow invocation selects this Skill but does not force full workflow overhead."
---

# AutoFlow

AutoFlow has two execution modes. Small, low-risk, single-module requests run directly from the relevant module contract. Connected or consequential work becomes an explicit artifact DAG whose dependencies, state transitions, approvals, and outputs are validated by deterministic scripts.

The repository layout and integration policy are documented in
`references/directory-layout.md`. Read it when adding or routing a capability.

Explicit invocation always wins: if the user asks for `autoflow`, use this Skill. It selects AutoFlow routing, not automatically the managed workflow mode.

## Core principles

- Compose only the modules the request needs: `task`, `image`, `word`, `ppt`, `video`, `package`.
- Use direct mode for small work; do not create workflow files or STOP gates merely because AutoFlow was named.
- Preserve decisions and evidence in files when the task actually needs a resumable managed workflow.
- In managed mode, treat `workflow.json` as a contract, not a narrative checklist.
- Complete real prerequisite work before writing downstream documents about it.
- Managed mode never infers approval from silence. Every PLAN, SOURCE, VISUAL, or DELIVERY request must first show its complete review packet.
- Register only real, validated artifacts. Placeholder code, mock evidence, and unverified deliverables do not count.
- This is AutoFlow Schema 1.0. Do not run legacy AutoLab workflow files.

## Read before acting

Always read:

1. `references/execution-modes.md`
2. The selected module file.

For direct mode, read only the route-specific guidance required by that module and execute the task. Do not initialize a run.

For managed mode, also read:

1. `references/workflow-contract.md`
2. `references/stop-gates.md`
3. `references/acceptance-contracts.md`
4. `references/anti-patterns.md`

Read `references/environment-contract.md` for project build or execution steps.

Then read only the modules selected for this run:

| Module | Read | Purpose |
|---|---|---|
| task | `modules/task.md` | Research, GitHub-first builds, computation, execution |
| image | `modules/image.md` | Capture, AI assets, diagrams, charts |
| word | `modules/word.md` | DOCX creation, editing, template filling |
| ppt | `modules/ppt.md` | PPTX creation/editing through the local audited presentation-skill integration |
| video | `modules/video.md` | Analysis, recording, creation, processing |
| package | `modules/package.md` | Requirement-driven delivery assembly |

AutoFlow also ships a local engineering-methodology layer under
`integrations/superpowers`. Before planning or executing a step, resolve the
exact local instructions with the CLI instead of invoking an external plugin:

```bash
python scripts/autoflow.py route --workflow <workflow.json> --step <step-id> --json --compact
```

To audit all checked-in external capabilities before planning, use:

```bash
python scripts/autoflow.py integrations --json
```

The command validates each integration manifest, declared Skill/reference
files, provenance fields, and adapter paths. A workflow must use the local
paths reported by `route`; a manifest or runtime marked unavailable is a hard
capability signal, not permission to invent a tool call.

Compact routing includes the module file, fresh verification, and required
capability adapters. It does not load every available methodology Skill. Use
`route --full` only when a specific TDD, debugging, security, performance, ADR,
or shipping method is needed. Independent or cross-model review is not part of
the default route.

Full routing may resolve the local `integrations/agent-skills` overlay for a
specific planning, interface, frontend, browser, observability, migration,
CI/CD, or debugging method. Compact routing does not load this overlay by
default. Read only the local paths returned by the selected route.

For independent build slices, set explicit step flags such as
`parallelizable`, `subagent_mode`, `git_worktree`, or `review_feedback`; the
route will add the corresponding local Superpowers collaboration guidance.
These flags never override DAG dependencies or STOP gates.

Frontend project steps may additionally resolve the integrated `impeccable`
design language and offline detector. Use the returned local adapter; never
fall back to `npx impeccable`, a remote URL scan, or an uninstalled plugin.

## Choose the execution mode

Make this decision before creating a request file, plan, run directory, or state file.

Use **direct mode** only when all of these are true:

- One module is sufficient.
- The request has one semantic artifact family. Editable source plus exports of the same diagram, such as `.mmd + .svg + .png`, still count as one family.
- There is no upstream/downstream dependency, GitHub source-selection decision, packaging contract, rubric-wide evidence map, or need to resume across steps.
- The work is low-risk and does not require a consequential, destructive, public, financial, or security-sensitive decision.
- The scope is already clear enough to execute without comparing materially different approaches.

In direct mode:

1. Do not run `autoflow init`.
2. Do not create `workflow.json`, `WORK_PLAN.md`, requirement maps, manifests, `.autoflow/`, or `submit/` unless the user explicitly requested that directory.
3. Resolve the checked-in local capability without a workflow:

```bash
python scripts/autoflow.py direct-route --module <module> --action <action> --json
```

4. Read the returned module and capability files, perform the real work, run the module's relevant quality check, and deliver the minimum requested output set at the user-requested path or current workspace. Do not expose extra source/export/report files unless requested or genuinely required.
5. Do not trigger PLAN, SOURCE, VISUAL, or DELIVERY STOP. Show the finished artifact and concise validation result once. Ask a targeted question only if a missing decision truly blocks execution.

Use **managed mode** when any direct-mode condition is false. Common triggers are multiple modules, dependent artifacts, GitHub-first project builds, packages/submission contracts, complex rubric or template evidence, multiple revision checkpoints, significant external side effects, or a user request for a resumable/auditable workflow.

When unsure, do not inflate a clearly small request. Choose managed mode only when the unresolved complexity changes scope, safety, dependencies, or acceptance.

## Start a managed run

1. Inspect the request and all supplied files before asking discoverable questions.
2. Choose the closest recipe:
   - `lab-report`: task → image → word → package
   - `report-and-slides`: task → image → word + ppt → package
   - `project-delivery`: GitHub discovery → build → image → package
   - `project-and-report`: GitHub discovery → build → image → word → package
   - `project-report-and-slides`: GitHub discovery → build → image → word + ppt → package
   - `video-delivery`: video → package
   - `document`: optional task/image → word
   - `presentation`: optional task/image → ppt
   - `custom`: Agent-authored DAG
3. Put the durable user request in a UTF-8 file. Do not rely on conversation memory alone.
4. Initialize:

```bash
python scripts/autoflow.py init \
  --request-file <request.md> \
  --output-dir <workspace>/autoflow \
  --recipe <recipe-or-auto>
```

5. Read the generated files from `<workspace>/autoflow/.autoflow/config/`: `workflow.json`, `run_state.json`, `artifact_manifest.json`, `requirement_map.json`, `delivery_review.json`, and `WORK_PLAN.md`.
6. If `auto` was used, inspect `workflow.json.recipe_selection`, including its matched signals and reason. Keep the recommended recipe when it fits; if it selected `custom`, replace its steps with the actual DAG before asking for approval.
7. Fill every `.autoflow/config/WORK_PLAN.md` section. Map each requirement or rubric item to declared evidence in `.autoflow/config/requirement_map.json`; record planned figures and real information substitutions rather than leaving these decisions implicit.
8. After editing workflow steps, synchronize the still-unstarted state and validate the configuration:

```bash
python scripts/autoflow.py sync --workflow <workspace>/autoflow/.autoflow/config/workflow.json
python scripts/autoflow.py validate --workflow <workspace>/autoflow/.autoflow/config/workflow.json
```

9. Build the PLAN review packet, present its substantive contents and paths, then stop:

```bash
python scripts/autoflow.py review \
  --workflow <workspace>/autoflow/.autoflow/config/workflow.json \
  --gate plan
```

Do not ask only “approve?” or “continue?”. Tell the user the goal, scope, recipe, ordered steps, expected outputs, important decisions/risks, and the absolute `WORK_PLAN.md` path. After explicit approval, record it:

```bash
python scripts/autoflow.py approve \
  --workflow <workspace>/autoflow/.autoflow/config/workflow.json \
  --gate plan \
  --note "<summary of the user's explicit approval>"
```

Do not start managed module work before PLAN_STOP approval.

## Execute the DAG

Ask AutoFlow which steps are ready:

```bash
python scripts/autoflow.py next --workflow <workspace>/autoflow/.autoflow/config/workflow.json
```

Resolve the local module and methodology route before acting on a ready step:

```bash
python scripts/autoflow.py route --workflow <workspace>/autoflow/.autoflow/config/workflow.json --step <step-id> --json --compact
```

For each ready step:

1. Read its module instructions.
2. Mark it running.
3. Perform the actual work.
4. Validate every declared output.
5. Complete it with exactly one artifact mapping for each declared output.

When multiple ready steps have no write conflict, prepare them together and run
their deterministic backends concurrently. In particular, run Word and PPT
build/render commands in parallel after shared image evidence is approved.
Do not introduce extra Agents to gain concurrency.

For project builds, run `environment_setup.py ensure` before baseline/build
commands. Keep the managed environment below `.autoflow/runtime/<step-id>/` and
register the ready `task.environment` report. Do not ask the user to install an
ordinary missing runtime or dependency.

Word steps must register both `word.document` and the matching `word.validation` report produced by `validate_word.py`. Follow the same report-first principle for video and package outputs described in `references/acceptance-contracts.md`.

```bash
python scripts/autoflow.py transition \
  --workflow <workspace>/autoflow/.autoflow/config/workflow.json \
  --step <step-id> \
  --to running

python scripts/autoflow.py transition \
  --workflow <workspace>/autoflow/.autoflow/config/workflow.json \
  --step <step-id> \
  --to completed \
  --artifact artifact.id=<absolute-path>
```

Use `--to blocked` when external input is genuinely required and `--to failed --note ...` when execution fails. Only optional steps may be skipped.

AutoFlow has no generic `run` command. The Agent invokes each module's real backend and uses the core CLI for state and validation.

## GitHub-first source selection

Code and runnable project tasks use separate `task.research` and `task.build` steps. Follow `modules/task.md` exactly.

- Search and inspect GitHub before implementation.
- Write `.autoflow/intermediate/plans/source_candidates.json` with real queries, scores, licenses, revisions, and judgments.
- Completing discovery activates SOURCE_STOP when usable candidates exist.
- Run `autoflow.py review --workflow ... --gate source`, show the 3–5 candidate comparison and source plan path, then wait for the user's selection.
- Record the selected candidate and revision before approving the gate.
- Clone and modify only after approval.
- If none are suitable, record rejected candidates and the reason for `from_scratch`; do not create a fake choice.

```bash
python scripts/autoflow.py approve \
  --workflow <workspace>/autoflow/.autoflow/config/workflow.json \
  --gate source \
  --note "User selected candidate <rank/name>"
```

## Visual review

In managed mode, any step with `gate_after: visual` activates VISUAL_STOP after completion. Run `autoflow.py review --workflow ... --gate visual`. Show the actual new artifacts, their purpose, paths, dimensions/page count/duration where applicable, validation results, visible concerns, and the exact decision needed. A filename-only or “please approve” message is invalid. Downstream Word, PPT, and packaging steps remain blocked until explicit approval.

```bash
python scripts/autoflow.py approve \
  --workflow <workspace>/autoflow/.autoflow/config/workflow.json \
  --gate visual \
  --note "User approved the displayed visual batch"
```

A later PPT or image batch reopens the same gate because it has not been reviewed yet.

## Delivery review

When all steps complete, AutoFlow activates DELIVERY_STOP. Before asking for approval:

- Run `autoflow.py review --workflow ... --gate delivery` and present the returned review packet.
- Run `validate` and resolve every error.
- Set `requirement_map.json.status` to `verified`, with every required item marked passed and backed by registered artifacts.
- Complete `delivery_review.json` with one result per required requirement and one result per registered artifact.
- Show final artifact paths and what requirement each satisfies.
- Inspect Word/PPT/media visually where applicable.
- List archive contents rather than assuming packaging succeeded.
- Confirm source code or applications actually run.
- State known limitations, or explicitly state that none remain.
- Provide the absolute `delivery_review.json` path. Never ask for sign-off with only a generic completion sentence.

After the user signs off:

```bash
python scripts/autoflow.py approve \
  --workflow <workspace>/autoflow/.autoflow/config/workflow.json \
  --gate delivery \
  --note "User approved the final delivery"
```

The run is complete only when `run_state.json.status` is `completed`.

## Status and recovery

```bash
python scripts/autoflow.py status --workflow <workspace>/autoflow/.autoflow/config/workflow.json
python scripts/autoflow.py status --workflow <workspace>/autoflow/.autoflow/config/workflow.json --timings
python scripts/autoflow.py eval-status --workflow <workspace>/autoflow/.autoflow/config/workflow.json
python scripts/autoflow.py validate --workflow <workspace>/autoflow/.autoflow/config/workflow.json --fast
python scripts/autoflow.py validate --workflow <workspace>/autoflow/.autoflow/config/workflow.json --deep
```

For evaluation runs, use `eval-status --expected-gate <gate>` when the test is
supposed to prove a STOP checkpoint. A `checkpoint_pass` is not a completed
end-to-end run; only `full_test_pass` may be reported as such.

Reuse hash-matched Word validation and PPT render caches. Use `--force` or
`--force-render` only after inputs or validation requirements change, or when
diagnosing a suspected cache defect.

- Never hand-edit `.autoflow/config/run_state.json` or `.autoflow/config/artifact_manifest.json` to bypass a gate.
- If the user rejects a STOP, record it with `autoflow.py gate --to rejected`, then use `autoflow.py revise --step <id> --reason <reason>` before regenerating terminal steps.
- If an artifact changes after registration, never refresh its hash by hand. Use `revise`; it supersedes target/downstream artifacts, resets requirement evidence, and reopens affected gates.
- A DELIVERY_STOP-approved run is immutable. Initialize a new revision run for later changes.
- If the integrated presentation runtime is missing, stop with a capability report rather than silently substituting a user-level or lower-quality backend.

## Prohibited actions and dangerous states

- Do not run tests, migrations, installers, or applications inside `submit/`.
- Do not place virtual environments, `node_modules`, caches, or runtime databases inside source artifacts.
- Do not package the workspace or `.autoflow/` by habit.
- Do not repeat full rendering, hashing, or packaging when inputs are unchanged.
- Do not invent approvals, source candidates, tool calls, or evidence.
- Do not turn a qualifying direct request into a managed run with control files and four STOP gates.
- Do not request STOP approval before showing the gate-specific review packet and its file paths.

Read `references/anti-patterns.md` for the complete replacement action for each prohibited state.

## Definition of done

For direct mode:

- The requested artifact family exists at the requested or clearly reported path.
- The relevant module-level quality check passed.
- No workflow control directory, plan, package, or STOP interaction was added without need.
- The user receives the artifact, path, and concise validation result in one completion message.

For managed mode:

- The selected recipe or custom DAG matches the request.
- Every STOP request first presented its required information and review paths; required approvals are recorded from explicit user responses.
- Every completed step has all declared artifacts.
- Artifact paths exist and hashes validate.
- Module-specific quality checks pass.
- Project environments are ready, verified, and outside source artifacts.
- Source/application tests ran before packaging in the isolated verification area.
- Final delivery passes `package_submission.py --verify-only` without modifying `submit/`.
- Every required requirement maps to present, correct evidence in `requirement_map.json` and `delivery_review.json`.
- `autoflow.py validate` returns `valid`.
- DELIVERY_STOP is explicitly approved.

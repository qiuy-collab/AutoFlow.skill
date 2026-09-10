<div align="center">

# AutoFlow.skill

A verifiable agent skill for multi-step delivery tasks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/qiuy-collab/AutoFlow.skill/actions/workflows/ci.yml/badge.svg)](https://github.com/qiuy-collab/AutoFlow.skill/actions)

**English · [简体中文](README.md)**

</div>

## What it is

AutoFlow gives compatible agent clients a workflow layer for
deliverable work. Research, code, screenshots, documents, slides, video and
packaging become a DAG with dependencies, approvals and hash-validated
artifacts.

The agent does the work. AutoFlow keeps the receipts — plans, state, approvals
and outputs live in files instead of chat history, so a run can be checked at
any point and resumed after interruption.

## Quick start

Give your agent:

```text
Use autoflow for this task. Read SKILL.md, pick a recipe, write WORK_PLAN.md
and wait for my approval. Do not skip the SOURCE, VISUAL and DELIVERY STOP gates.
```

Or drive the CLI directly:

```bash
python scripts/autoflow.py init \
  --request-file request.md \
  --output-dir autoflow \
  --recipe auto

python scripts/autoflow.py next \
  --workflow autoflow/.autoflow/config/workflow.json

python scripts/autoflow.py status \
  --workflow autoflow/.autoflow/config/workflow.json
```

## STOP gates

AutoFlow stops at four checkpoints. Before each approval it shows a reviewable
packet — evidence and paths, not a bare "ok?":

- **PLAN** — scope, steps, expected artifacts
- **SOURCE** — GitHub candidates for code tasks
- **VISUAL** — images, diagrams, visual slides
- **DELIVERY** — final manifest, sign-off

If no GitHub candidate fits, AutoFlow keeps the queries and exclusion reasons
and builds from scratch. It does not invent candidates to keep the pipeline
moving.

## Modules

`task` · `image` · `word` · `ppt` · `video` · `package`

Compose them into recipes — `lab-report`, `project-delivery`,
`report-and-slides`, `custom` DAGs. The workflow contract lives in
[`references/workflow-contract.md`](references/workflow-contract.md).

## What it is not

- Not a low-code platform — that's n8n / Coze / Dify
- Not a graph framework — that's LangGraph
- Not an "everything in one command" runner — there is no pretend-done mode.
  Every artifact is checked before it ships.

## Layout

```text
SKILL.md        routing entry point
modules/        task, image, word, ppt, video, package
recipes/        built-in DAG templates
references/     workflow, STOP, acceptance, environment contracts
integrations/   vendored, version-pinned capabilities
scripts/        state machine, adapters, backends
tests/          unit & integration tests
examples/       real delivery samples
docs/           GitHub Pages
```

## Test

```bash
python -m unittest discover -s tests
```

## License

[MIT](LICENSE) © [qiuy-collab](https://github.com/qiuy-collab)

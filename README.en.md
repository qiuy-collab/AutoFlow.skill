<div align="center">

# AutoFlow.skill

**A verifiable Agent Skill for multi-step delivery tasks.**

Orchestrate code, diagrams, documents, slides, video and packaging into one
inspectable, interruptible, resumable workflow.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/qiuy-collab/AutoFlow.skill)](https://github.com/qiuy-collab/AutoFlow.skill/releases)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/qiuy-collab/AutoFlow.skill/actions/workflows/ci.yml/badge.svg)](https://github.com/qiuy-collab/AutoFlow.skill/actions)

</div>

## What is this?

AutoFlow is a **Skill for AI agents** (Claude Code, Codex, NewMax, and any
agent that can load Skills). It turns multi-step delivery work — research,
coding, screenshots, reports, slides, video and submission packages — into an
explicit workflow graph with dependencies, state transitions, approvals and
hash-validated artifacts.

AutoFlow does **not** make decisions for the agent. It records the plan,
dependencies, approvals and artifacts that would otherwise scatter across a
chat, so a complex task can be **reviewed** and **resumed after interruption**.

For example, "build a student management system, write the paper, then make
the defense slides" becomes: source research → project build → screenshots →
paper → slides → packaging. Every step has explicit inputs, outputs and
acceptance criteria; source selection, visual results and final delivery stop
and wait for *your* confirmation.

It also fits lab reports, project deliveries, data-analysis reports,
presentations, video assignments, and custom tasks that produce multiple
artifacts. For a single file edit or a simple question, AutoFlow is usually
overkill.

## Why AutoFlow?

| Concern | n8n / Coze / Dify | LangGraph | **AutoFlow** |
|---|---|---|---|
| Human-in-the-loop approval gates | Platform-bound | Build it yourself | **Built-in STOP gates** |
| Verifiable, hash-checked artifacts | ❌ | ❌ | ✅ Built-in |
| Resume after interruption | Partial | Manual | ✅ Durable state |
| Works natively inside an agent chat | ❌ (external platform) | Library, DIY wiring | ✅ Agent Skill |
| 6 delivery modules (task/image/word/ppt/video/package) | Visual nodes | DIY | ✅ Composable recipes |

## Quick Start

Give your agent this line together with your task:

```text
Use autoflow for this task. Read SKILL.md, choose a recipe, write WORK_PLAN.md
and wait for my approval. Do not skip the SOURCE, VISUAL and DELIVERY STOP gates.
```

Or initialize manually:

```bash
python scripts/autoflow.py init \
  --request-file request.md \
  --output-dir autoflow \
  --recipe auto

python scripts/autoflow.py status \
  --workflow autoflow/.autoflow/config/workflow.json

python scripts/autoflow.py validate \
  --workflow autoflow/.autoflow/config/workflow.json
```

Inspect the next executable steps and local capability routing:

```bash
python scripts/autoflow.py next \
  --workflow autoflow/.autoflow/config/workflow.json

python scripts/autoflow.py route \
  --workflow autoflow/.autoflow/config/workflow.json \
  --step <step-id> --json --compact

python scripts/autoflow.py integrations --json
```

> Note: legacy AutoLab `workflow.json` files are incompatible with AutoFlow
> Schema 1.0 and must be re-initialized.

## The six modules

| Module | What it does |
| --- | --- |
| `task` | Research, GitHub source selection, project build, computation, real execution |
| `image` | Screenshots, AI images, flow/architecture diagrams, scientific figures, charts |
| `word` | DOCX creation, editing, template filling, structure validation |
| `ppt` | PPTX creation, editing, rendering, visual QA |
| `video` | Video analysis, screen recording, generation, transcoding, media validation |
| `package` | Assemble `submit/` per delivery requirements, manifest and archive |

Modules compose freely. Built-in recipes plus custom DAGs:

| Recipe | Flow |
| --- | --- |
| `lab-report` | task → image → word → package |
| `report-and-slides` | task → image → word + ppt → package |
| `project-delivery` | GitHub discovery → build → image → package |
| `project-and-report` | GitHub discovery → build → image → word → package |
| `project-report-and-slides` | GitHub discovery → build → image → word + ppt → package |
| `video-delivery` | video → package |
| `document` | optional task/image → word |
| `presentation` | optional task/image → ppt |
| `custom` | any DAG generated from the request |

## Two execution modes

AutoFlow does not force every request through a full workflow.

- **Direct mode**: a single module, a single semantic artifact, no
  dependencies or consequential choices → read the module rules, generate,
  verify and deliver. No plan files, state files, `submit/` or STOP gates are
  created.
- **Managed mode**: multiple modules or connected artifacts, GitHub source
  selection, submission packages, complex scoring/template mapping, recovery
  and audit needs, or consequential external decisions → initialize a DAG
  with STOP gates.

Explicitly writing "use autoflow" selects AutoFlow routing, not necessarily
Managed mode. Direct mode can be inspected without creating any workflow file:

```bash
python scripts/autoflow.py direct-route \
  --module image --action diagram --json
```

## How it works

Each run lives in its own `autoflow/` directory:

```text
autoflow/
├── .autoflow/
│   ├── config/          # workflow, state, approvals, requirement mapping
│   ├── intermediate/    # plans, intermediates, logs, verification reports
│   ├── runtime/         # auto-provisioned isolated runtime
│   └── scripts/         # task-specific scripts
└── submit/              # final deliverables
```

The agent understands the task, calls tools and does the real work; the Python
CLI validates the DAG, state transitions, approval gates and artifact hashes.
There is deliberately **no** "pretend everything is done" `run` command.

Managed mode has four STOP gates that keep the human in control. Before every
request for approval, the agent must show a reviewable packet (evidence +
paths), never just ask "ok?":

- `PLAN_STOP` — confirm scope, steps and expected artifacts before starting.
- `SOURCE_STOP` — for code tasks, list GitHub candidates; the user picks one
  before cloning/rebuilding.
- `VISUAL_STOP` — images, diagrams or visual slides are shown before they flow
  into downstream documents.
- `DELIVERY_STOP` — after all checks pass, show the delivery manifest; the
  workflow ends only when the user signs off.

Generate the review packet with the CLI:

```bash
python scripts/autoflow.py review \
  --workflow autoflow/.autoflow/config/workflow.json \
  --gate plan
```

If no suitable GitHub candidate exists, AutoFlow keeps the queries and
exclusion reasons and builds from scratch — it never fabricates candidates to
keep the workflow moving.

## Built-in capabilities

Key runtime capabilities are vendored into the repo with pinned upstream
revisions, licenses and local adapters. No hidden assumptions about which
external Skill is installed, and no "I called it successfully" claims in text
alone.

Current integrations:

- `minimax-docx` — DOCX/OpenXML creation, template handling, structural validation.
- `nature-figure` — scientific schematics and figure types.
- `presentation-skill` — PPTX generation, rendering, visual QA.
- `webapp-testing` — Playwright-based web testing with screenshot evidence.
- `impeccable` — frontend design rules and offline quality checks.
- `superpowers`, `agent-skills`, `engineering-quality` — planning, debugging,
  testing, security, performance and shipping methodology.

AI images read AutoFlow's own `.env` upstream config (no OpenRouter
dependency). Missing environments are auto-provisioned by modules into
`.autoflow/runtime/` — never into the final delivery directory.

Environment check:

```bash
python scripts/env_setup.py --check-only --route all --no-probe
```

## Repository layout

```text
autoflow/
├── SKILL.md             # routing entry point
├── modules/             # task / image / word / ppt / video / package
├── recipes/             # built-in DAG templates
├── references/          # workflow, STOP, acceptance and environment contracts
├── integrations/        # audited, version-pinned built-in capabilities
├── scripts/             # state machine, adapters, module backends
├── tests/               # unit & integration tests
├── evals/               # scenario evaluations
├── examples/            # example configs and real delivery samples
└── docs/                # GitHub Pages and screenshots
```

See [`references/directory-layout.md`](references/directory-layout.md) for
detailed directory responsibilities and
[`references/workflow-contract.md`](references/workflow-contract.md) for the
workflow schema.

## Showcase

### Generated documents

![Generated documents](docs/效果图/生成的文档截图.png)

### Final delivery directory

![Delivery files](docs/效果图/交付文件.png)

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
```

Coverage includes: DAG and cycle detection, state transitions, all four STOP
gates, GitHub with/without candidates, environment auto-provisioning,
Word/PPT/video acceptance, image and scientific-figure routing, sensitive-file
rejection, isolated re-runs, and packaging that ships only declared artifacts.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).

## License

[MIT License](LICENSE) © [qiuy-collab](https://github.com/qiuy-collab)

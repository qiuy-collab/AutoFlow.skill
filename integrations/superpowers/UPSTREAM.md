# Superpowers integration

AutoFlow integrates a curated, file-only subset of `obra/superpowers`.

- Upstream: https://github.com/obra/superpowers
- Revision: `d884ae04edebef577e82ff7c4e143debd0bbec99`
- Upstream release: `v6.1.1`
- License: MIT; see `LICENSE`
- Integrated on: 2026-07-17

Included sub-skills are `brainstorming`, `writing-plans`,
`test-driven-development`, `systematic-debugging`,
`verification-before-completion`, `requesting-code-review`,
`executing-plans`, `finishing-a-development-branch`,
`dispatching-parallel-agents`, `subagent-driven-development`,
`using-git-worktrees`, `receiving-code-review`, and `using-superpowers`.

AutoFlow intentionally does not copy the upstream plugin bootstrap, hooks,
telemetry, package metadata, or agent-specific installation files. The
AutoFlow CLI is the only runtime router; `scripts/autoflow.py route` returns
the local files relevant to a workflow step.

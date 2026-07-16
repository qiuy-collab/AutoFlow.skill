# AutoFlow adapter contract

The copied `SKILL.md` files are upstream methodology references. AutoFlow
binds them to its own execution contract as follows:

| AutoFlow point | Integrated guidance | Enforcement or route |
|---|---|---|
| Before `PLAN_STOP` | `brainstorming`, `writing-plans` | `autoflow.py route` and `WORK_PLAN.md` |
| `task.build` / `task.execute` | `test-driven-development` | task plan and verification evidence |
| `blocked` / `failed` | `systematic-debugging` | failure plan in `plans/` before retry |
| Every completion claim | `verification-before-completion` | artifact validators and fresh commands |
| Between engineering steps | `requesting-code-review` | read-only review route before the next step |
| Approved plan execution | `executing-plans` | AutoFlow DAG and `next`/`transition` |
| Delivery handoff | `finishing-a-development-branch` | `DELIVERY_STOP` and package review |
| Independent implementation slices | `dispatching-parallel-agents` / `subagent-driven-development` | Explicit step routing and isolated evidence |
| Build isolation | `using-git-worktrees` | Build step with `git_worktree: true` |
| Review feedback | `receiving-code-review` | Explicit review/rework route before transition |
| Skill discovery | `using-superpowers` | Global route context |

References in upstream text such as `superpowers:<name>` are informational
labels. In AutoFlow, resolve the corresponding local file under this
directory and record the resulting plan/evidence in the run directory. Do not
invoke an uninstalled external plugin as a substitute.

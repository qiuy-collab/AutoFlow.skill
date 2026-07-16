# AutoFlow adapter contract

| AutoFlow route | Impeccable capability | Result |
|---|---|---|
| `task.build` with `design_backend` | project context, design register, command references | local design plan and implementation guidance |
| `image.capture` with `design_backend` | responsive and visual quality review | local detector findings and visual evidence inputs |
| `image` visual review | `audit`, `critique`, `polish`, `harden`, `adapt` references | review findings stored in the run's `plans/` or evidence directory |

The adapter runs only local Node scripts. It sets
`AUTOFLOW_IMPECCABLE_OFFLINE=1`, rejects HTTP(S) targets, and never invokes
`npx`, plugin hooks, telemetry, or automatic updates. Findings do not
automatically approve a VISUAL_STOP; the user gate remains authoritative.

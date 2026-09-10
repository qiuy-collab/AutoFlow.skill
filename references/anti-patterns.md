# Prohibited actions and dangerous states

These rules are hard failures, not suggestions.

| Prohibited action | Required replacement |
|---|---|
| Initialize a managed run for a qualifying one-module, one-artifact-family request | Use `direct-route`, read the module rules, execute, validate, and deliver without control files or STOP gates. |
| Ask for any STOP approval with only “ready/approve/continue” | Run `autoflow.py review --gate ...` and present the gate-specific information, artifacts, validation, and absolute review paths first. |
| Hand-edit `run_state.json` or `artifact_manifest.json` | Use `transition`, `approve`, `gate`, or `revise`. |
| Modify an artifact after registration | Run `autoflow.py revise --step ... --reason ...`; never refresh the hash by hand. |
| Execute tests, migrations, installers, or applications in `submit/` | Test in `.autoflow/intermediate/verification/`, then package once. |
| Put `.venv`, `venv`, `node_modules`, caches, or package-manager state inside source artifacts | Provision under `.autoflow/runtime/<step-id>/`. |
| Zip the workspace or AutoFlow control directory | Package only declared include paths with requirement mappings. |
| Ask the user to install a normal runtime or dependency | Follow [environment initialization](init.md), inspect the project manifest, and run the required install and verification commands first. |
| Invent GitHub candidates, tool calls, evidence, or STOP approvals | Record only observed sources, commands, artifacts, and explicit user responses. |
| Run write-producing commands after final packaging | Use `package_submission.py --verify-only`. |
| Repeat complete rendering, hashing, or packaging when inputs are unchanged | Reuse validated outputs; use fast validation during iteration and deep validation at gates. |
| Report a run waiting at a STOP as a completed end-to-end evaluation | Use `eval-status`; report `checkpoint_pass` separately and reserve `full_test_pass` for completed workflows. |
| Force Word validation or PPT rendering on unchanged inputs by default | Reuse fingerprinted caches; force only for changed policy or cache diagnosis. |
| Retry a failed step indefinitely | Respect its per-revision `max_attempts`; diagnose the repeated failure, then reopen it with `revise`. |
| Load every integrated methodology Skill for every step | Use compact routing; request `--full` only when a specific method is needed. |
| Mark an upstream package integrated while runtime code still comes from a user Skill or source checkout | Copy the required local core into `integrations/`, declare every path, and pass the self-containment catalog. |
| Pass object-shaped `sections` to the integrated Word create command | Use the executable's flat `heading` / `paragraph` / `pagebreak` array contract. |
| Pass an unverified or character style to `insert-paragraph --style` | Resolve an existing paragraph style ID/name first; unknown styles must fail. |
| Reject required template instructions merely because they remain in a filled output | Compare instruction matches with the template baseline and reject only newly introduced matches. |
| Call a subset-XSD failure an XSD pass | Record the business-rules fallback explicitly and require rendered visual review. |

If a prohibited action has already occurred, stop downstream execution. Revise the earliest affected step, invalidate downstream evidence, and regenerate delivery from that point.

# AutoFlow STOP gates

STOP gates protect decisions that should not be inferred from silence.

## PLAN_STOP

Always active after initialization. Fill all sections of `WORK_PLAN.md`, align `workflow.json` to the actual request, show the plan to the user, and wait. Approve only after an explicit response.

## SOURCE_STOP

Activated when GitHub discovery finds usable candidates. Show the candidate table and ask the user to choose. Before approval, update `plans/source_candidates.json` with the confirmed choice and selected revision. If no candidate is suitable, record the search and fallback; the gate becomes not applicable and implementation starts from scratch.

## VISUAL_STOP

Activated by a completed step with `gate_after: visual`. Show every new image/deck batch to the user. Approval applies only to the current artifact hashes; completing a later visual step activates the gate again.

## DELIVERY_STOP

Activated after every workflow step is completed or skipped and no earlier STOP remains. Show the artifact list, paths, validation results, and package contents. Approving it marks the run completed.

## Approval integrity

`autoflow.py approve` requires a non-empty note, but the Agent remains responsible for provenance: execute it only after the user explicitly approves. If the user rejects a gate, record the rejection, revise the affected plan or artifact, and do not continue downstream.

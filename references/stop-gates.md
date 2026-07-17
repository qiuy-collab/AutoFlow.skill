# AutoFlow STOP gates

STOP gates protect decisions that should not be inferred from silence.

## PLAN_STOP

Always active after initialization. Fill all sections of `.autoflow/config/WORK_PLAN.md`, align `.autoflow/config/workflow.json` to the actual request, and complete `.autoflow/config/requirement_map.json` with requirement-to-evidence and planned-figure mappings. Show the plan to the user and wait. Approve only after an explicit response.

## SOURCE_STOP

Activated when GitHub discovery finds usable candidates. Show the candidate table and ask the user to choose. Before approval, update `.autoflow/intermediate/plans/source_candidates.json` with the confirmed choice and selected revision. If no candidate is suitable, record the search and fallback; the gate becomes not applicable and implementation starts from scratch.

## VISUAL_STOP

Activated by a completed step with `gate_after: visual`. Show every new image/deck batch to the user. Approval applies only to the current artifact hashes; completing a later visual step activates the gate again.

## DELIVERY_STOP

Activated after every workflow step is completed or skipped and no earlier STOP remains. Verify `requirement_map.json`, complete `delivery_review.json`, and show the artifact list, paths, validation results, and package contents. Approval is rejected unless every required requirement and registered artifact is present and correct. Approving it marks the run completed.

The final package is frozen before this gate. After publication, only read-only
validation is allowed. Any write beneath `submit/` invalidates delivery: revise
the package step, verify the source in isolation, package once, then activate a
new delivery gate for the new hashes.

## Revision after a gate or completed step

Do not edit registered artifacts or state files in place. Run `autoflow.py
revise --workflow ... --step <earliest-affected-step> --reason ...`. AutoFlow
supersedes current hashes, reopens the target and downstream steps, and resets
the affected gates. A previous approval never applies to revised artifact
hashes.

## Approval integrity

`autoflow.py approve` requires a non-empty note, but the Agent remains responsible for provenance: execute it only after the user explicitly approves. If the user rejects a gate, record the rejection, revise the affected plan or artifact, and do not continue downstream.

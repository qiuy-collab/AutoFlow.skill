# AutoFlow STOP gates

STOP gates belong only to managed mode. Direct mode has no STOP gates.

A STOP protects a consequential decision; it is not a ritual confirmation. Before asking the user to decide, generate the gate review packet:

```bash
python scripts/autoflow.py review --workflow <workflow.json> --gate <plan|source|visual|delivery>
```

Present the packet in the user's language. A message that only says “ready”, “approve?”, “continue?”, or “reply yes” is invalid. Include clickable absolute paths when the client supports them. The user must be able to judge the decision without opening hidden control files, while the paths let them inspect the full evidence.

## PLAN_STOP

Always active after managed initialization. Fill all sections of `.autoflow/config/WORK_PLAN.md`, align `.autoflow/config/workflow.json` to the actual request, and complete `.autoflow/config/requirement_map.json`.

Before asking for approval, show:

- What the task will produce and the success criteria.
- Selected recipe and ordered module/action steps.
- Expected deliverables, paths or types, and requirement mappings.
- Decisions already made, decisions still open, exclusions, risks, and important constraints.
- The absolute path to `WORK_PLAN.md` and supporting workflow/requirement files.

Then ask the user to approve the plan or identify the exact scope, step, or output to revise. Approve only after an explicit response.

## SOURCE_STOP

Activated when GitHub discovery finds usable candidates. Before asking for a selection, show:

- Real search queries and evaluation criteria.
- Three to five candidate names with repository links.
- Scores, license, pinned revision, requirement fit, buildability, modification distance, maintenance signal, and risks.
- A recommendation with a concrete reason; recommendations never replace the user's choice.
- The absolute path to `source_candidates.json`.

Ask the user to select a rank, reject all candidates, or request another search. Before approval, update `source_candidates.json` with the confirmed choice and selected revision. If no candidate is suitable, show the search/exclusion summary and fallback reason; record `from_scratch` and mark this gate not applicable without inventing a choice.

## VISUAL_STOP

Activated by a completed visual step in managed mode. Before asking for approval, show:

- The actual new images, rendered slides, or sampled video frames—not filenames alone.
- Each artifact's purpose and downstream use.
- Absolute paths and useful facts such as dimensions, page count, duration, or format.
- Validation results, visible issues, and what changed since the previous review.
- The exact visual decision required from the user.

Ask the user to approve the displayed batch or give concrete revision feedback per artifact. Approval applies only to the current artifact hashes; completing or revising another visual artifact activates a new review. Downstream consumers remain blocked until approval.

## DELIVERY_STOP

Activated after every managed workflow step is completed or skipped and no earlier STOP remains. Before asking for sign-off, show:

- Final deliverable inventory with clickable absolute paths.
- Requirement-to-artifact mapping and whether every required item passed.
- Build/test/run results plus Word, PPT, image, video, and package validation relevant to this delivery.
- Archive contents and sensitive-file scan result when a package exists.
- Known limitations, or an explicit statement that none remain.
- The absolute path to `delivery_review.json` and supporting manifest/requirement map.

Ask the user to sign off the delivery or identify the exact deliverable/requirement to revise. Approval is rejected unless every required requirement and registered artifact is present and correct. Approving it marks the run completed.

The final package is frozen before this gate. After publication, only read-only validation is allowed. Any write beneath `submit/` invalidates delivery: revise the package step, verify the source in isolation, package once, and activate a new delivery gate for the new hashes.

## Revision after a gate or completed step

Do not edit registered artifacts or state files in place. Run:

```bash
python scripts/autoflow.py revise \
  --workflow <workflow.json> \
  --step <earliest-affected-step> \
  --reason <reason>
```

AutoFlow supersedes current hashes, reopens the target and downstream steps, and resets affected gates. A previous approval never applies to revised artifact hashes.

## Approval integrity

`autoflow.py approve` requires a non-empty note, but the Agent remains responsible for provenance. Execute it only after the user explicitly approves the review packet. If the user rejects a gate, record the rejection, revise the affected plan or artifact, and do not continue downstream.

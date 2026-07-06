# Visual Review Rules

This document defines the mandatory visual acceptance pass for `auto-lab`.

## Decision owner

- Visual review is an agent reasoning step.
- The agent must inspect the generated images directly before marking review-complete fields.
- Script validation should fail if the checklist claims review is complete but the agent has not actually inspected the images.

## AI screenshot review

Before setting `ai_visual_review_completed = true`, check every `ai_simulated` image for:
- readable text at a normal report zoom level
- only necessary information, not a high-density wall of tiny UI
- a believable background instead of an empty cutout scene
- a consistent environment/background style across the full image set unless the requirement explicitly needs scene changes
- pixel-level sharpness with crisp text and clean UI edges
- no blur, haze, soft-focus wash, mosaic blocks, or blocky compression artifacts
- consistent timestamps or time-of-day cues when the same operation session is being shown
- no `localhost`, `127.0.0.1`, dev URLs, tabs, or address bars unless explicitly required
- no malformed icons, twisted controls, broken charts, warped tables, or obviously fake UI details

If any item fails:
- revise the prompt
- regenerate only the failed image via a supplement prompt config, not the full batch
- review again

## Diagram review

Before setting `diagram_visual_review_completed = true`, check every `diagram_assets` image for:
- clean spacing
- no overlapping labels
- no modules, text blocks, or arrows colliding after final render
- no accidental line crossings unless intentionally unavoidable
- readable labels
- line routing that looks deliberate rather than tangled
- enough empty space around each node so the diagram still looks clean inside the report page

If any item fails:
- revise the node layout, explicit edge path, or canvas spacing
- regenerate the diagram
- review again

## Browser capture review

Before setting `browser_visual_review_completed = true`, check every `browser_capture` image for:
- the page reads like the actual site/app rather than a lab handout shell
- no visible `lab1`, `lab2`, `exp1`, `exp2`, or similar experiment-stage labels unless the requirement explicitly asks for them
- no note panels, report wording, instructional copy, or explanation blocks that belong in the report instead of the frontend
- no obvious debug/dev scaffolding that distracts from the actual page content
- no `localhost`, `127.0.0.1`, dev URLs, tabs, or address bars unless explicitly required
- the screenshot focuses on the real user flow and the page state needed by the report
- text is readable and the page looks intentional rather than placeholder-heavy

If any item fails:
- adjust the frontend presentation or page content first
- recapture only the affected screenshots
- review again

## Output contract

- `ai_visual_review_completed` may be `true` only after AI screenshot review passes
- `browser_visual_review_completed` may be `true` only after browser screenshot review passes
- `diagram_visual_review_completed` may be `true` only after diagram review passes

# Visual Review Rules (Human-only)

This document defines the mandatory human visual review pass for `auto-lab`.

## Decision owner

- **Visual review is a human decision step — NOT an agent step.**
- The agent must STOP after image generation and present all generated images to the human user.
- The agent must NOT self-evaluate image quality, mark review-complete flags, or proceed to DOCX insertion without explicit human approval.
- The agent must wait for the human to explicitly confirm: "images approved" or provide fixup instructions.

## Workflow

```
[Image generation completes]
        ↓
🔴 STOP #2 — Agent displays all generated images to human
        ↓
Human reviews images:
  ├─ Approved → Agent proceeds to DOCX insertion
  ├─ Needs clarity fix → Agent runs img2img with fixed clarity prompt → back to STOP #2
  ├─ Needs content fix → Agent runs img2img single-point replacement → back to STOP #2
  └─ Needs full regeneration → Agent revises prompt_config.json → regenerates → back to STOP #2
```

## Human review dimensions

The human reviewer should check each image for:

### AI screenshot review

| # | Check item | Pass condition |
|---|-----------|----------------|
| 1 | Text readability | Readable at normal report zoom level |
| 2 | Information density | Only necessary information, not a high-density wall of tiny UI |
| 3 | Background believability | Believable background, not an empty cutout scene |
| 4 | Environment consistency | Consistent background/style across the full image set |
| 5 | Pixel sharpness | Crisp text and clean UI edges |
| 6 | No visual artifacts | No blur, haze, mosaic blocks, or blocky compression |
| 7 | Time consistency | Consistent timestamps/time-of-day cues within same session |
| 8 | Real URLs | URLs shown are the application's real access URLs |
| 9 | No malformed UI | No twisted controls, broken charts, warped tables |
| 10 | No AI-origin exposure | No text like "AI生成" or "示意图" visible |

### Diagram review

| # | Check item | Pass condition |
|---|-----------|----------------|
| 1 | Clean spacing | Nodes not touching each other |
| 2 | No overlapping labels | All labels readable without overlap |
| 3 | No element collisions | Text blocks, arrows not colliding |
| 4 | No accidental line crossings | Lines cross only when intentionally unavoidable |
| 5 | Readable labels | All labels clear (Chinese renders correctly) |
| 6 | Deliberate routing | Lines look intentional, not tangled |
| 7 | Sufficient whitespace | Enough empty space around each node |

### Browser capture review

| # | Check item | Pass condition |
|---|-----------|----------------|
| 1 | Page authenticity | Reads like real site/app, not a lab handout shell |
| 2 | No lab-stage labels | No `lab1`/`exp1`/`exp2` labels unless required |
| 3 | No report content in page | No note panels, report wording, instructional copy |
| 4 | No debug scaffolding | No distracting dev/debug elements |
| 5 | Real URLs | URLs are the application's real access URLs |
| 6 | User flow focus | Screenshot captures real user flow and required page state |
| 7 | Text readability | Text is readable, page looks intentional |

## Fixup types (agent executes, human triggers)

### Type 1: Clarity fix (不清晰)

When an image is blurry or pixelated:

- Use the fixed clarity-enhancement prompt from `C:\Users\ASUS\Desktop\补图提示词--不清晰.md`
- Run img2img with the blurry original as `reference_image`
- The prompt ensures: original content unchanged, only sharpness/readability enhanced

### Type 2: Content fix (内容错误)

When an image has a specific content error:

- Run img2img with a **single-point replacement prompt**
- Describe only the element to fix; explicitly state "keep original structure intact"
- The original (incorrect) image is the `reference_image`

## Output contract

- The agent must NOT set `ai_visual_review_completed`, `diagram_visual_review_completed`, or `browser_visual_review_completed` to `true` on its own.
- These flags are set to `true` ONLY after the human explicitly approves all images.
- The agent records the human's approval in `approval_checkpoints.json` and only then updates the review-completed flags needed by the workflow.

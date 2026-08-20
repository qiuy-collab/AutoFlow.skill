# Visual Review Rules (Human-only)

This document defines the mandatory human `VISUAL_STOP` review for AutoFlow.

## Decision owner

- **Visual review is a human decision step — NOT an agent step.**
- The agent must STOP after image generation and present all generated images to the human user.
- The agent may run deterministic quality checks, but must not approve the gate or proceed to downstream consumers without explicit human approval.
- The agent must wait for the human to explicitly confirm: "images approved" or provide fixup instructions.

## Workflow

```
[Image generation completes]
        ↓
🔴 VISUAL_STOP — Agent displays all generated images to human
        ↓
Human reviews images:
  ├─ Approved → Agent proceeds to DOCX insertion
  ├─ Needs clarity fix → Agent runs img2img with fixed clarity prompt → back to VISUAL_STOP
  ├─ Needs content fix → Agent runs img2img single-point replacement → back to VISUAL_STOP
  └─ Needs full regeneration → Agent revises the image plan → regenerates → back to VISUAL_STOP
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

- Write a clarity-enhancement prompt that keeps the original content and
  composition unchanged and only increases sharpness and readability
- Run img2img with the blurry original as `reference_image`
- The prompt ensures: original content unchanged, only sharpness/readability enhanced

### Type 2: Content fix (内容错误)

When an image has a specific content error:

- Run img2img with a **single-point replacement prompt**
- Describe only the element to fix; explicitly state "keep original structure intact"
- The original (incorrect) image is the `reference_image`

## Output contract

- The Agent must not set `run_state.json.gates.visual.status=approved` on its own.
- After explicit approval, run `autoflow.py approve --gate visual --note ...`; the note must summarize the user's actual response.
- Completing a later image or PPT step activates VISUAL_STOP again for the new artifact hashes.

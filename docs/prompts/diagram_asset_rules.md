# Diagram Asset Rules (DSL-driven)

This document defines how `AutoFlow image.diagram` should write a plan and generate diagram assets.

## Architecture

Diagrams are generated via **DSL code → professional renderer → PNG/SVG**, never via PIL hand-drawing.

```
diagram_plan.json → generate_diagram_assets.py
  ├─ kind=flowchart      → Mermaid (.mmd) → mmdc → PNG/SVG
  ├─ kind=er_diagram     → Mermaid (.mmd) → mmdc → PNG/SVG
  ├─ kind=data_flow_diagram → D2 (.d2) → d2 → PNG/SVG
  ├─ kind=function_diagram  → D2 (.d2) → d2 → PNG/SVG
  ├─ kind=architecture_diagram → D2 (.d2) → d2 → PNG/SVG
  └─ kind=uml_diagram    → PlantUML (.puml) → plantuml → PNG/SVG
```

## Renderer Mapping

The mapping below is a set of convenience templates, not a whitelist. When a
diagram needs a Mermaid, D2, or PlantUML feature that has no JSON template,
use the arbitrary DSL route:

```json
{
  "name": "custom_state_machine",
  "kind": "state_machine",
  "renderer": "mermaid",
  "source": "stateDiagram-v2\n    [*] --> Draft\n    Draft --> Published\n    Published --> [*]"
}
```

`renderer` must be `mermaid`, `d2`, or `plantuml`; `source` is passed through
unchanged and is saved alongside the rendered PNG/SVG. This route supports any
diagram type supported by the selected renderer.

```python
RENDERER_MAP = {
    "flowchart": "mermaid",
    "er_diagram": "mermaid",
    "data_flow_diagram": "d2",
    "function_diagram": "d2",
    "architecture_diagram": "d2",
    "uml_diagram": "plantuml",
}
```

## Scope boundary

`diagram_plan.json` is only for the `image.diagram` action.

Use it for:
- function diagrams (功能图)
- flowcharts (流程图)
- data flow diagrams (数据流图)
- ER diagrams (ER图)
- architecture diagrams (架构图)
- UML diagrams (类图/用例图/时序图/组件图/部署图)

Do NOT use it for:
- terminal screenshots
- command output screenshots
- local frontend page screenshots
- third-party product screenshots
- AI-generated images when a deterministic DSL or real capture is required.
  AI scientific schematics are handled by the `image.ai` scientific-figure
  route, not by this diagram plan.

## Planning order

1. Read the requirement document.
2. Read the diagram step and its declared input artifacts.
3. Complete required task steps and absorb their outputs.
4. Decide which figures belong to `image.diagram`.
5. For each diagram, define semantic structure (no absolute coordinates):
   - `name` (used as filename prefix)
   - `kind` (a built-in semantic template, or any custom semantic label)
   - `renderer` + `source` (required for arbitrary native DSL diagrams)
   - `title` (diagram caption)
   - `direction` (TD / LR — for flowcharts)
   - `nodes[]` (with id, label, shape)
   - `edges[]` (with from, to, optional label)
   - `entities[]` / `relations[]` (for ER diagrams)

## diagram_plan.json format

### Flowchart example

```json
{
  "enabled": true,
  "diagrams": [
    {
      "name": "login_flow",
      "kind": "flowchart",
      "title": "用户登录流程图",
      "direction": "TD",
      "nodes": [
        {"id": "start", "label": "开始", "shape": "start"},
        {"id": "input", "label": "输入账号和密码", "shape": "process"},
        {"id": "check", "label": "验证账号密码", "shape": "decision"},
        {"id": "success", "label": "进入系统首页", "shape": "process"},
        {"id": "fail", "label": "提示登录失败", "shape": "process"},
        {"id": "end", "label": "结束", "shape": "end"}
      ],
      "edges": [
        {"from": "start", "to": "input"},
        {"from": "input", "to": "check"},
        {"from": "check", "to": "success", "label": "正确"},
        {"from": "check", "to": "fail", "label": "错误"},
        {"from": "fail", "to": "input"},
        {"from": "success", "to": "end"}
      ]
    }
  ]
}
```

Node shapes: `start`/`end` → `([...])`, `process` → `[...]`, `decision` → `{...}`, `data` → `[/.../]`, `subprocess` → `[[...]]`.

### ER diagram example

```json
{
  "name": "student_er",
  "kind": "er_diagram",
  "title": "学生选课 ER 图",
  "entities": [
    {
      "name": "STUDENT", "label": "学生",
      "attributes": [
        {"type": "int", "name": "student_id", "key": "PK"},
        {"type": "string", "name": "name"},
        {"type": "string", "name": "class_name"}
      ]
    },
    {
      "name": "COURSE", "label": "课程",
      "attributes": [
        {"type": "int", "name": "course_id", "key": "PK"},
        {"type": "string", "name": "course_name"}
      ]
    }
  ],
  "relations": [
    {"from": "STUDENT", "to": "COURSE", "type": "}o--o{", "label": "选修"}
  ]
}
```

## Output contract

Each diagram generates BOTH source and image files:

```
output/images/login_flow.mmd
output/images/login_flow.svg
output/images/login_flow.png

output/images/system_architecture.d2
output/images/system_architecture.svg
output/images/system_architecture.png

output/images/user_case.puml
output/images/user_case.png
```

## Run command

```bash
python scripts/generate_diagram_assets.py --config plans/diagram_plan.json --output-dir artifacts/diagrams
```

## Prerequisites

Check these tools are installed before running. If missing, show friendly install hints:

| Tool | Install command |
|------|----------------|
| Mermaid CLI (`mmdc`) | `npm install -g @mermaid-js/mermaid-cli` |
| D2 (`d2`) | `winget install Terrastruct.D2` or https://d2lang.com/tour/install |
| PlantUML (`plantuml`) | Requires Java; `winget install OpenJDK.OpenJDK.17` then install PlantUML |

## Quality rules

- White or transparent background
- Clear, readable Chinese text (no garbled characters)
- Sufficient spacing between nodes — not cramped
- Arrow directions clearly distinguishable
- Module hierarchy visually apparent
- No label overlaps, no accidental line crossings
- Prefer SVG output first, PNG as fallback
- The diagram must look clean when inserted into a Word report or PPT slide
- Priority: **Accuracy > Maintainability > Aesthetics > Automation**

## Diagram review (before insert)

Before inserting a diagram into the report, check:
- clean spacing — no elements touching each other
- no overlapping labels
- no modules, text blocks, or arrows colliding after final render
- no accidental line crossings unless intentionally unavoidable
- readable labels (Chinese characters render correctly)
- line routing looks deliberate rather than tangled
- enough empty space around each node

## Output contract

`diagram_plan.json` should:
- match only the `image.diagram` artifacts
- keep names aligned with `copywriting.md` placeholders
- never include AI screenshot figures or browser-capture figures
- stay free of comments and helper fields
- all diagrams share one `enabled` flag at the top level

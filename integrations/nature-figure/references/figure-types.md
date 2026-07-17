# Nature Figure classification inside AutoFlow

Nature Figure is integrated under the existing AutoFlow `image` module. It is
classified, but never treated as an optional external Skill after routing.

## `image.chart` publication templates

Five deterministic Python templates are executable through
`integrations/nature-figure/scripts/plot_templates.py`:

- `volcano`
- `roc`
- `dotplot`
- `marginal`
- `paired`

Production runs consume real CSV data. `--demo` exists only for deterministic
integration testing and its QA record must identify the data as simulated.
Each run exports editable SVG, PDF, 600-DPI TIFF, and QA JSON.

## `image.chart` adaptable scientific patterns

Radar/polar, 3D conceptual geometry, cluster scatter, probability-manifold,
ablation-line, fill-between area, log-scale bar, multi-metric/grouped bars,
event-annotated trends, and multi-panel compositions are adaptation patterns.
They require task data and a run-specific plotting source; they are not falsely
advertised as fixed CLI templates.

## `image.ai` scientific schematics

- `graphical_abstract`
- `mechanism_diagram`
- `concept_illustration`
- `paper_schematic`

These use AutoFlow's `.env` image upstream with `gpt-image-2`, never
OpenRouter. They are conceptual drafts and cannot invent quantitative evidence.

## Full-test rule

AutoFlow image regression must cover every executable category together:

1. real capture smoke;
2. AI txt2img/img2img contract plus all scientific-schematic prompt kinds;
3. all built-in and custom deterministic diagram kinds;
4. all five publication-chart templates and their export/QA contracts.

A passing DSL diagram suite alone is not a passing image module suite.

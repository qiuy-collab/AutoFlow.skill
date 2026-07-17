---
name: nature-figure
description: AutoFlow-local publication chart and scientific schematic backend integrated from nature-figure 2.1.0.
---

# Integrated Nature Figure

This is an internal AutoFlow image capability, not a separate user-level call.

- Route quantitative publication figures through `image.chart` and
  `scripts/plot_templates.py` in this integration.
- Route graphical abstracts, mechanism diagrams, concept illustrations, and
  paper schematics through `image.ai` and AutoFlow's
  `scripts/generate_scientific_schematic.py`.
- Keep deterministic structured architecture/UML/ER/process diagrams in
  `image.diagram`.
- Validate publication plotting source with
  `scripts/validate_scientific_figure.py` before delivery.

Read `references/figure-types.md` for the complete classification and testing
boundary. Every executable type in `figure-types.json` belongs to the unified
AutoFlow image coverage matrix.

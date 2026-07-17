# nature-figure integration provenance

- Upstream: https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure
- Integrated revision: `fb3bffa0b5d299b939fae959786e222bf699bd25`
- License: Apache-2.0; see `LICENSE`.
- Integrated components: scientific-figure contract and type taxonomy, all five validated publication-chart templates, backend preference logic, source preflight rules, and AI schematic prompt contract.
- Deliberate change: the OpenRouter client is not included. `scripts/generate_scientific_schematic.py` uses AutoFlow's existing `.env` `BASEURL`/`APIKEY` upstream and `gpt-image-2` through `scripts/generate_images.py`.

AutoFlow owns the routed workflow and validation contracts. This directory is
an internal implementation plus attribution record, not a separately invoked
user-level Skill.
The copied plotting runtime is locally callable from this integration and is
covered by AutoFlow's unified image test matrix; it does not depend on the
separate upstream checkout at runtime.

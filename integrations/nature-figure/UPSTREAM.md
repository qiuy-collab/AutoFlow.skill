# nature-figure integration provenance

- Upstream: https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure
- Integrated revision: `fb3bffa0b5d299b939fae959786e222bf699bd25`
- License: Apache-2.0; see `LICENSE`.
- Integrated components: scientific-figure contract and type taxonomy, backend preference logic, source preflight rules, and AI schematic prompt contract.
- Deliberate change: the OpenRouter client is not included. `scripts/generate_scientific_schematic.py` uses AutoFlow's existing `.env` `BASEURL`/`APIKEY` upstream and `gpt-image-2` through `scripts/generate_images.py`.

AutoFlow owns the routed workflow and validation contracts. This directory is attribution metadata, not a separately invoked Skill.

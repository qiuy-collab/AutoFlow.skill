# agent-skills integration provenance

- Upstream: https://github.com/addyosmani/agent-skills
- Integrated revision: `c1974de476a39cb002a3b8e51e6a7e8e57b808c6`
- License: MIT; see `LICENSE`.
- Integrated components: 15 standalone workflow Skills and seven supporting
  checklists used by AutoFlow's route resolver.
- Deliberately excluded: upstream plugin manifests, slash commands, agents,
  hooks, setup scripts, telemetry, and runtime bootstrap. AutoFlow reads the
  copied local Markdown only and never installs or invokes the upstream plugin.

The eight overlapping quality Skills remain under
`integrations/engineering-quality` or `integrations/superpowers` so there is a
single canonical local path for each existing route.

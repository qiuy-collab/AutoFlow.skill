# AutoFlow image routing taxonomy

All visual capabilities remain inside the `image` module. Integration changes
implementation ownership, not module boundaries.

| Action | Internal family | Canonical backend |
|---|---|---|
| `capture` | browser/application/terminal evidence | integrated webapp testing or deterministic local capture |
| `ai` | general txt2img/img2img | AutoFlow image upstream |
| `ai` | Nature scientific schematics | integrated nature-figure contract + AutoFlow upstream |
| `diagram` | structured DSL diagrams | Mermaid, D2, PlantUML |
| `chart` | ordinary computed charts | task data + local plotting code |
| `chart` | Nature publication templates | integrated nature-figure Python templates |

Full image validation is the union of these families. No integration may be
excluded merely because its implementation lives under `integrations/`.

# AutoFlow integration self-containment contract

Every directory under `integrations/` is part of the AutoFlow package. Once an
upstream capability is integrated, normal routing must not depend on a
user-level Skill installation, a temporary source checkout, or an undeclared
adapter file.

Each `integration_manifest.json` must declare:

- `mode`: `integrated_local_runtime` or `integrated_instruction_overlay`;
- `self_contained: true`;
- `external_user_skill_required: false`;
- `source_checkout_required: false`;
- every routed Skill, reference, and adapter path needed by AutoFlow;
- upstream revision and license for provenance only.

Operating-system runtimes and language dependencies may remain provisioned
dependencies when bundling them would be inappropriate. AutoFlow must detect
and automatically provision them through its environment layer; this does not
permit resolving executable code from another Skill directory.

`autoflow.py integrations --json` rejects missing declarations, unsafe paths,
files outside the package, and adapter source that points at known user-Skill
or source-checkout locations. A new integration is not routable until the
catalog reports `available`.

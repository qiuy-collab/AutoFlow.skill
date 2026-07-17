# Impeccable integration

AutoFlow integrates the local, provider-neutral Impeccable Skill and its
deterministic frontend detector.

- Upstream: https://github.com/pbakaus/impeccable
- Revision: `8259c28209b92792005cec14dad573df39f68eaf`
- Upstream Skill version: `3.9.1`
- License: Apache-2.0; see `LICENSE`
- Third-party attribution: see `NOTICE.md`
- Integrated on: 2026-07-17

The upstream provider bootstrap, plugin hooks, automatic update checks, and
remote URL scan mode are not part of AutoFlow's runtime. Use
`scripts/impeccable_adapter.mjs` as the only entry point.

# AutoFlow integration record

- Upstream: https://github.com/anthropics/skills/tree/main/skills/webapp-testing
- Revision: `9d2f1ae187231d8199c64b5b762e1bdf2244733d`
- Integrated path: `integrations/webapp-testing`
- License: Apache-2.0; see `LICENSE.txt`
- Adaptation: the upstream skill and helper are preserved as an integrated
  capability. AutoFlow routes frontend capture plans to this fixed path and
  checks both the helper and the local Playwright runtime before PLAN_STOP.
- Generation date: 2026-07-17

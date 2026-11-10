---
summary: Decide whether --global installs are deprecated or ship the deploy tool
status: blocked
owner: 
since: 
plan: 
depends: []
decisions: []
---
Goal: Resolve how memory and doctor run after a --global install.
Scope: A --global install has no launcher, so memory and doctor run only as ./deploy from a source checkout (docs/deploy.md). Deprecate --global installs, or ship the deploy tool with them.
Done when: The decision is recorded and implemented.
Notes: Blocked: owner decision pending; the owner leans toward deprecation (2026-10-29). Source: .supervisor/archive/working/plans/externalize-memory.md (D15, D19).

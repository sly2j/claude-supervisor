---
domain: process
summary: Only .supervisor/roadmap.md migrates to task cards automatically; a root ROADMAP.md gets a follow-up suggestion and is never moved
affects: [pack/skills/project-memory/references/curator-procedures.md]
verified: 2026-11-10
source: .supervisor/archive/working/plans/plan-task-cards.md (user 2026-11-10)
supersedes:
---
Curator migrates the store roadmap in the default-branch checkout on any run and reports its cards; a root `ROADMAP.md` only adds `follow-up: curator migrate ROADMAP.md`.
Why: the store roadmap is the product's own format; a root file is the project's page and may serve readers.
Rejected: moving a root `ROADMAP.md` unasked; migrating from a feature-branch checkout.

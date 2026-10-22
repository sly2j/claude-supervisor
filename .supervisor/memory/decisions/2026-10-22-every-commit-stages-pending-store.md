---
domain: process
summary: Every commit in a project checkout also stages that checkout's pending .supervisor/ changes, except mid-conflict
affects: [pack/skills/repo-workflow/SKILL.md, pack/skills/git-safety/references/conflict-resolution.md]
verified: 2026-10-22
source: user 2026-10-22, .supervisor/archive/working/plans/plan-store-persistence.md#decisions
supersedes: 
---
D2. Every commit in a project checkout, on any branch, also stages that checkout's pending `.supervisor/` changes, except while resolving a conflict. This gives "the store is committed" an owner on the default branch. Risk: a commit can carry another stage's half-written store file, so reports list the store paths they committed. Rejected: a commit per default-branch store write (a `VERSION` bump per entry).

Reach: product; `pack/skills/repo-workflow/SKILL.md` (Store changes).

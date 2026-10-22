---
domain: process
summary: Store merge conflicts keep both sides of history.md and plan Logs; one entry changed on both sides keeps the default-branch text
affects: [pack/skills/git-safety/references/conflict-resolution.md]
verified: 2026-10-22
source: user 2026-10-22, .supervisor/archive/working/plans/plan-store-persistence.md#decisions
supersedes: 
---
D4. Store conflicts: `history.md` and a plan `## Log` keep both sides' lines; other files combine per the normal conflict steps; one entry changed differently on both sides keeps the default-branch text and the report names the branch text with `follow-up: curator`. Never drop an entry file.

Reach: product; `pack/skills/git-safety/references/conflict-resolution.md`.

---
domain: process
summary: One file per entry; kinds decision, fact, lesson, goal, convention; no index file
affects: [pack/skills/project-memory/]
verified: 2026-10-22
source: docs/archive/plan-memory-v2.md#scope-notes
supersedes: 
---
D11, as amended at landing. One file per entry, replacing the single-file `docs/decisions.md`.
Kinds are `decision`, `fact`, `lesson`, `goal`, `convention`, each with a `domain:` (`code`,
`writing`, `science`, `process`). A goal stays active until met or dropped, then moves to the
archive. There is no generated `memory/INDEX.md` (dropped at planning, OQ8): kind folders plus one
`grep -r '^summary:'` over `memory/` list the store, always current and never a merge conflict.
Program logs go in each plan's `## Log`, replacing a separate logbook.

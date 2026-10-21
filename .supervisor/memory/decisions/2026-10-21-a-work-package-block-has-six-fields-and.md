---
domain: process
summary: A work package block has six fields and one Status value per stage; no owner, estimate or priority
affects: [pack/agents/planner.md, README.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-wbs.md#scope-notes
supersedes:
---
A package block has exactly six fields: Goal, Owns (disjoint across packages), Deps, Stages (an ordered subset of research, plan, execute, write), Status, Artifacts. Stage names map onto the four leads, so there is no lead field. `Status` is the stage due next, `blocked: <stage>: <why>`, or `done`; that single value serves both dispatch and resume with one ready rule. `planner` fills `Artifacts` at plan time, so `supervisor` takes output paths from the block and never carries a naming convention. The schema is stated once, in `planner.md`; other files refer to it or show a filled example.

Rejected as creep: a `pending`/`running` status pair, extra fields (owner, estimate, priority), extra status values (`ready`, `waiting`), a stage-to-lead table in `supervisor.md`, a status mirror in the plan's `## Todo` (duplicate state, two edits per transition), and a phrase lint for the section.

Reach: product; stated in pack/agents/planner.md:52-69.

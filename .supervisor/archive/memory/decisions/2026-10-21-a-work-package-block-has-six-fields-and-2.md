---
domain: process
summary: A work package block has six fields and one Status value per stage; no owner, estimate or priority; stated once in the plan-writing skill
affects: [pack/skills/plan-writing/SKILL.md, pack/agents/planner.md, README.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-planner-lighter-plans.md#decisions
supersedes: .supervisor/archive/memory/decisions/2026-10-21-a-work-package-block-has-six-fields-and.md
---
A package block has exactly six fields: Goal, Owns (disjoint across packages), Deps, Stages (an ordered subset of research, plan, execute, write), Status, Artifacts. Stage names map onto the four leads, so there is no lead field. `Status` is the stage due next, `blocked: <stage>: <why>`, or `done`; that single value serves both dispatch and resume with one ready rule. `planner` fills `Artifacts` at plan time, so `supervisor` takes output paths from the block and never carries a naming convention.

Since 3.0 the schema, its Status values and the integration and child-plan shape lines are stated once, in `pack/skills/plan-writing/SKILL.md` (`## Work Packages`); `planner.md` keeps only the split rules (when to split, parallel preference, user override, `Amend parent:`, single approval) and points to the skill. Other files refer to the skill or show a filled example (README).

Rejected as creep: a `pending`/`running` status pair, extra fields (owner, estimate, priority), extra status values (`ready`, `waiting`), a stage-to-lead table in `supervisor.md`, a status mirror in the plan's `## Todo` (duplicate state, two edits per transition), and a phrase lint for the section.

Reach: product; stated in pack/skills/plan-writing/SKILL.md.
dropped: 2026-10-22 (memory audit: covered by pack/, CLAUDE.md or docs, or no longer a live claim)

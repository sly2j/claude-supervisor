---
domain: process
summary: The supervisor runs work packages as a program in waves; the parent plan file is the only state
affects: [pack/agents/supervisor.md, pack/agents/planner.md, docs/architecture.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-wbs.md#approach
supersedes:
---
Work too large for one plan carries a `## Work Packages` section. `supervisor` runs it as a program: each wave sends every package whose `Status` names a stage and whose `Deps` are `done` to that stage's lead, all at once; after the wave one write-back advances each finished package's `Status`. The user sees a package table per wave, and a lead's open question blocks only its package until the user answers.

State: the parent plan file is the only program state, so a fresh session resumes from it. `supervisor` never reads the plan; it holds one line per package (id, Deps, Stages, Status, Artifacts), returned by `planner` after writing or amending the plan, or by one `scout` call on resume. Leads write only their package's artifact, so the parent plan has one writer at a time.

Rejected: a coordinator agent (the owner decided supervisor owns the loop); continuous per-return advancement instead of waves (unbounded report cadence, harder resume); a `program-loop` skill or reference file (the rules fit in a few bullets in `supervisor.md`); `planner` syncing status per transition (an expensive model for a one-line edit); supervisor editing plans itself (all project changes go through agents).

Reach: product; stated in pack/agents/supervisor.md:75-90 and docs/architecture.md:60.

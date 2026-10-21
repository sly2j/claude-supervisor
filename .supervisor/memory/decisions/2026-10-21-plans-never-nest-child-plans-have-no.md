---
domain: process
summary: Plans never nest: child plans have no packages; a split amends the parent plan
affects: [pack/agents/planner.md, docs/architecture.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-wbs.md#approach
supersedes:
---
Agent depth stays supervisor, lead, worker, and the plan tree stays two levels. A package's child plan is a normal plan with no `## Work Packages` section. A package that turns out to need its own breakdown is split by its `planner` returning an `Amend parent:` block (the complete new package blocks, `Deps` on the split package so their `execute` stage receives its child plan as input, and the changed lines), never by editing the parent; the supervisor's write-back step applies the block, serialised with the wave's status edits. An amendment too large for that step escalates and re-routes to a `planner` annotation cycle on the parent.

Why: depth is bounded structurally rather than by a counter, and the single serialised writer avoids write contention on the parent plan. Integration work is itself a package, so the loop handles one kind of thing.

Reach: product; stated in pack/agents/planner.md:70-72 and docs/architecture.md:60.

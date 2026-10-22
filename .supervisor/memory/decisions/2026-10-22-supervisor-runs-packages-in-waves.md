---
domain: process
summary: The supervisor runs work packages in waves with the parent plan as the only state
affects: [pack/agents/supervisor.md, pack/agents/planner.md, docs/architecture.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-wbs.md; owner 2026-10-21
supersedes: .supervisor/archive/memory/decisions/2026-10-22-program-flow-rationale.md
---
A fresh session resumes from the parent plan file; the supervisor never reads the plan and one writer at a time touches it.
Why: bounded report cadence and easy resume. Rejected: a coordinator agent (the owner decided supervisor owns the loop), continuous per-return advancement, a `program-loop` skill, the planner syncing status per transition (expensive model for a one-line edit), the supervisor editing plans itself.

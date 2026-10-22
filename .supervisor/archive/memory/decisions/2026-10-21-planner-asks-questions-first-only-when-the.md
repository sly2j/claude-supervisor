---
domain: process
summary: The planner two-steps (first pass, then full plan) only on an open question or design fork; the first pass gets Review: light and blocks only on questions that survive
affects: [pack/agents/planner.md, pack/skills/plan-writing/SKILL.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-planner-lighter-plans.md#decisions
supersedes:
---
Owner answers 2026-10-21 (D6). When the brief leaves an open question or a design fork, the first pass holds `## Goal`, `## Approach`, `## Decisions`, `## Open Questions` (each with a recommended answer) and the slice headings only. It gets `Review: light`, which checks each question: answerable from the repo, the research artifact or memory, or only by the user. The planner answers the answerable ones itself, moves them to `## Decisions` with the evidence, and continues to the full plan; it returns Outcome `blocked` only with the surviving questions. Answers return in a re-dispatch brief through the supervisor's batching. Otherwise the plan is written in one pass. `supervisor.md` is untouched; the report's next-action line (answer, then re-dispatch `planner`) guards against routing a blocked report to `executor`.

Rejected: one pass with questions left open (the status quo); the planner asking the user directly (bypasses the supervisor's single user channel); a design stage in the package block (reopens the six-field decision).

Reach: product; written into pack/agents/planner.md (`## Questions First`).
superseded by: .supervisor/memory/decisions/2026-10-22-program-flow-rationale.md

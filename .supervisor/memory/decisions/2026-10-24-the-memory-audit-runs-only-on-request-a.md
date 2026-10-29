---
domain: process
summary: The memory audit runs only on request; a size or count threshold trigger was rejected
affects: [pack/skills/project-memory/references/curator-procedures.md, pack/agents/curator.md]
verified: 2026-10-29
source: user 2026-10-22 (.supervisor/archive/working/plans/plan-memory-bloat.md#scope-notes)
supersedes: .supervisor/archive/memory/decisions/2026-10-22-audit-runs-on-request-only.md
---
The audit is started by the user, never by a store-size or entry-count threshold.
Why: the user wants the timing of a bulk cleanup in their hands.
Rejected: a threshold trigger.

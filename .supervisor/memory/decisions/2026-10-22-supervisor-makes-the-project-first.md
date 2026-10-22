---
domain: process
summary: Supervisor dispatches curator make this a project before a session's first store-writing stage
affects: [pack/agents/supervisor.md, pack/agents/planner.md, pack/agents/researcher.md]
verified: 2026-10-22
source: user 2026-10-22, .supervisor/archive/working/plans/plan-store-persistence.md#decisions
supersedes: 
---
D6 (user, options b and c). In a project, before the session's first store-writing stage, `supervisor` dispatches `curator` `make this a project`, with no existence check because D5 is idempotent. The supervisor's bullet carries the detection rule in one sentence, and `planner` and `researcher` point to `project-memory` (Projects and one-offs) beside their path rules. Why: deciders never saw the detection rule, so nothing created or committed the store. Rejected: preloading `project-memory` into more agents (about 910 words of context).

Reach: product; `pack/agents/supervisor.md`, `planner.md`, `researcher.md`.

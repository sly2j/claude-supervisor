---
domain: process
summary: Only curator creates the store; supervisor dispatches make-this-a-project before its first store write
affects: [pack/agents/curator.md, pack/agents/supervisor.md, pack/skills/project-memory/SKILL.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-store-persistence.md#decisions; user 2026-10-22
supersedes: .supervisor/archive/memory/decisions/2026-10-22-store-lives-in-the-branch-curator-commits.md
---
The dispatch has no existence check; the curator is idempotent.
Why: deciders never saw the detection rule, so nothing created or committed the store. Rejected: preloading `project-memory` into more agents (about 910 words of context).
superseded by: .supervisor/memory/decisions/2026-10-23-store-lives-in-the-branch.md

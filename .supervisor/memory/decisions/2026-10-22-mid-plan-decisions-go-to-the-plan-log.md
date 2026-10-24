---
domain: process
summary: Mid-plan decisions go to the plan Log and reach memory only through the recording test at close-out
affects: [pack/agents/supervisor.md, pack/skills/plan-writing/SKILL.md, pack/agents/clerk.md]
verified: 2026-10-24
source: user 2026-10-22 (.supervisor/archive/working/plans/plan-memory-bloat.md#decisions)
supersedes: .supervisor/archive/memory/decisions/2026-10-21-the-post-wave-clerk-records-mid-program.md
---
User answers and binding lead decisions are logged as `decision:` lines in the plan Log; close-out filters them through the recording test.
Why: recording each at once through the clerk filled the store with plan-time one-offs. Risk: a plan that never closes keeps them in its Log; the idle-plan sweep surfaces it.

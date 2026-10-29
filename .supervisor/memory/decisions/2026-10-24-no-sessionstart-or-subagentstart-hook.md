---
domain: process
summary: No SessionStart or SubagentStart hook injects memory; add one only after a relevant entry was observed missed at contract time
affects: [pack/agents/supervisor.md]
verified: 2026-10-29
source: .supervisor/archive/working/plans/plan-memory-v2.md#open-questions
supersedes: .supervisor/archive/memory/decisions/2026-10-21-no-retrieval-hooks-in-v2-0-add-one-only.md
---
Memory reaches agents through leads reading it at contract time and `scout` reading it for the supervisor, not through an injecting hook.
Why: no failure has been observed yet. Add a hook (in `supervisor.md` frontmatter) only after a relevant entry was seen missed at contract time.

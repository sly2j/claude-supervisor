---
domain: process
summary: The supervisor preloads no skill, so supervisor.md is the only copy of its routing and bookkeeping rules; a skill restating one does not make it redundant there
affects: [pack/agents/supervisor.md]
verified: 2026-10-27
source: .supervisor/archive/working/research/research-supervisor-word-budget.md
supersedes:
---
The supervisor runs as the main thread with no `skills:` field, so `lead-loop`, `project-memory`, `git-safety`, `repo-workflow`, `plan-writing` and `agent-authoring` reach it only if it loads them on demand.
A word-budget or redundancy audit of `supervisor.md` therefore counts a line as redundant only when it repeats an agent description (which the supervisor sees in the Agent tool's listing) or built-in tool guidance. A skill or agent that states the same rule does not qualify.
Rejected: moving the Programs section into a skill loaded on demand, because on-demand loading is less reliable than the always-present body for wave scheduling.

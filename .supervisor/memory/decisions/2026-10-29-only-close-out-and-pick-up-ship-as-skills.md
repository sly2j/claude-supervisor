---
domain: process
summary: Only /close-out and /pick-up ship as user-invoked lifecycle skills; other lifecycle prompts stay prose
affects: [pack/skills/close-out/, pack/skills/pick-up/, docs/workflow-lifecycle.md]
verified: 2026-10-29
source: .supervisor/archive/working/plans/workflow-lifecycle.md
supersedes:
---
The two lifecycle prompts that every observed flow needed, phrased differently each time, are skills: `/close-out [retry]` and `/pick-up [<plan path>]`, run in the supervisor's own context (no forked context). Opening a task, approving, asking for state and tearing down stay plain requests.
Why: close-out needed a typed nudge in every flow, and a terse follow-up after `/clear` sent the supervisor hunting for the plan; extra skills add surface without an observed failure.
Rejected: one `/lifecycle <verb>` skill (a verb mini-language); `/session-state`, open and `/tear-down` skills; `resume` as a name (a built-in command would shadow it).

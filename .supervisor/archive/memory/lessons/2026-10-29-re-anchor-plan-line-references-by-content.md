---
domain: process
summary: Plan line references go stale when the default branch moves mid-run; executors re-anchor by content or commit hash, never by line number alone.
affects: [pack/skills/plan-writing/SKILL.md, pack/skills/lead-loop/SKILL.md]
verified: 2026-10-29
source: user 2026-10-29
supersedes:
---
A plan that cites line numbers names the commit they were taken against, and the executor re-locates each target by content or by that commit's hash before editing or diffing.
Why: a commit landed on the default branch between planning and execution, so a relative-commit diff check would have compared the wrong commit; the executor found the right one by hash.
Product behaviour: the pack's plan-writing and lead-loop do not yet state this rule; it is still to be written there, and this entry expires when it is.
superseded by: pack/skills/plan-writing/SKILL.md

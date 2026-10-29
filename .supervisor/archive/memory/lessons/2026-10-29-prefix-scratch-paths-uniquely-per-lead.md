---
domain: process
summary: Leads running in parallel share one session scratchpad; each prefixes its scratch files uniquely so review diffs do not collide.
affects: [pack/skills/lead-loop/SKILL.md, pack/agents/executor.md]
verified: 2026-10-29
source: user 2026-10-29
supersedes:
---
Parallel leads (for example executors in separate worktrees) share the session scratchpad, so each names its scratch files with a prefix unique to its lead or unit.
Why: a shared diff filename collided in a critic round, and the reviewer had to rule from the worktree files instead.
Product behaviour: the pack's lead-loop and executor definition do not yet state this rule; it is still to be written there, and this entry expires when it is.
superseded by: pack/skills/lead-loop/SKILL.md

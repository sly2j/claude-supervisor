---
domain: process
summary: Leads write their own log line; quick-tier dispatches are not logged
affects: [pack/skills/lead-loop/SKILL.md, pack/agents/supervisor.md, pack/agents/clerk.md]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#approach
supersedes: 
---
When the brief names a plan, a lead's report ends with `Log:` and a ready-made `## Log` line,
which the post-wave `clerk` appends unchanged; the supervisor never summarizes deferrals. The lead
knows what it deferred and why. Quick-tier dispatches (clerk, git-ops, scout) and curator runs are
not logged: they defer and decide nothing, and git shows them. Accepted 2026-10-18.
dropped: 2026-10-22 (memory audit: covered by pack/, CLAUDE.md or docs, or no longer a live claim)

---
domain: process
summary: Executor runs on Sonnet by default; supervisor passes model opus per dispatch only for difficult work
affects: [pack/agents/executor.md, pack/agents/supervisor.md, pack/skills/agent-authoring/SKILL.md, docs/architecture.md]
verified: 2026-10-29
source: user 2026-10-27
supersedes:
---
The executor lead is a cheap default with an expensive escalation, the mirror of the writer rule (expensive default, cheap opt-down). Opus is for multi-module design, large or unfamiliar refactors, hard conflicts, subtle debugging and agent design; never for well-specified or mechanical changes.
Why: the user's usage panel ranked executor the largest subagent consumer (25% of subagent usage) and recommended a cheaper model; the tool audit over the first days of the current pack shows the executor lead holds about 88% of the executor tree's tokens (workers about 5%) and its critic passed round 1 in 5 of 5 runs, so quality headroom exists.
Open: no Sonnet baseline exists, so the saving is projected; re-run `tools/audit/audit.py` after a few days on Sonnet and compare the executor tree and its critic round-1 pass rate.

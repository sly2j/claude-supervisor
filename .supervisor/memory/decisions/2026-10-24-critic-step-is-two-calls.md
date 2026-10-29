---
domain: process
summary: The lead's critic step is two calls (once-per-task probe, then per-round Codex call) so Claude-mode users never see codex; scope-critic stays on Claude
affects: [pack/skills/lead-loop/SKILL.md, pack/skills/supervisor-config/scripts/codex-critic]
verified: 2026-10-29
source: .supervisor/archive/working/plans/plan-codex-critic.md, user 2026-10-24
supersedes: 
---
The probe runs once per task and the Claude `critic` agent is the fallback on any Codex failure. Claude-mode users never see the word codex.
`scope-critic` stays on Claude: in a seeded test neither Codex model recognised scope creep as such.
Rejected: a single combined call; moving scope-critic to Codex.

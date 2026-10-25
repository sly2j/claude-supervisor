---
domain: process
summary: Codex critic is opt-in only, never auto-enabled because codex is on PATH; consent covers OpenAI quota and repository content sent to OpenAI
affects: [deploy, pack/skills/supervisor-config/]
verified: 2026-10-24
source: .supervisor/archive/working/plans/plan-codex-critic.md, user 2026-10-24
supersedes: 
---
The Codex critic turns on only when the user runs the switch command or `deploy critic enable` and says yes. Presence of `codex` on PATH never enables it; install only prints a hint.
Why: reviews spend the user's OpenAI quota and send repository content to OpenAI, so the user must consent first.
Rejected: auto-detecting Codex and enabling it.

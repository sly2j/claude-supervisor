---
domain: process
summary: git-ops stays a separate agent and is not folded into the supervisor; the owner prefers fixing git-safety to removing the agent
affects: [pack/agents/git-ops.md, pack/skills/git-safety/SKILL.md]
verified: 2026-10-24
source: user 2026-10-24 (owner decision after .supervisor/archive/working/research/research-fold-subagents.md)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-git-ops-stays-separate-fix-git-safety.md
---
Why: git work is discardable context (diffs, logs), and its safety rules conflict with the supervisor's. The owner saw the same needless git-ops stops on other machines and wants those fixed in git-safety (the rules live there), not the agent removed.
Rejected: folding git into the supervisor.

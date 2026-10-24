---
domain: process
summary: git-ops stays a separate agent; fix git-safety instead (own same-session commits may be amended; a brief naming what to stage ignores unrelated untracked files)
affects: [pack/agents/git-ops.md, pack/skills/git-safety/SKILL.md]
verified: 2026-10-24
source: user 2026-10-24 (owner decision after .supervisor/working/research/research-fold-subagents.md)
supersedes:
---
Do not fold git into the supervisor. Change the git-safety rules: a commit created earlier in the same supervisor session counts as the session's own and may be amended or reset; a brief that names exactly what to stage is not stopped by unrelated untracked files from sibling agents.
Why: git work is discardable context (diffs, logs) and its safety instructions conflict with the supervisor's. The owner sees the same needless git-ops stops on other machines.

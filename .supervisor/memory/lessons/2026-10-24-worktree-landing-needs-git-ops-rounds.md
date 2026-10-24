---
domain: process
summary: landing a one-file change from a worktree took three git-ops rounds; land with git push origin HEAD:main, and expect git-safety stops on same-session amends and sibling untracked files
affects: [pack/skills/git-safety/SKILL.md, pack/agents/git-ops.md]
verified: 2026-10-24
source: user 2026-10-24
supersedes:
---
Landing a one-file change from a worktree took three git-ops rounds. The harness confines the session to the worktree, so land with `git push origin HEAD:main`, never via the parent checkout. git-safety refused to amend a same-session commit, and it stopped on a sibling agent's untracked file.
Why: the last two stops are what decision `.supervisor/memory/decisions/2026-10-24-git-ops-stays-separate-fix-git-safety.md` fixes in git-safety; until that lands, expect them and name the files to stage in the brief.

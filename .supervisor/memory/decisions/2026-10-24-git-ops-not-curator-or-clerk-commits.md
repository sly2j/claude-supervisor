---
domain: process
summary: git-ops, not curator or clerk, commits memory writes
affects: [pack/agents/curator.md, pack/agents/clerk.md, pack/agents/git-ops.md, pack/skills/git-safety/]
verified: 2026-10-24
source: user 2026-10-23 ("should curator and clerk be doing commits in the first place? That's git-ops job"; approved the proposal: "yes, that sounds good")
supersedes: .supervisor/archive/memory/decisions/2026-10-23-only-git-ops-commits-memory-writes-2.md
---
Why: the attribution rule lived only in `git-safety`, which curator and clerk neither preload nor can load (no Skill tool), so Claude Code's default model-name trailer won and they refused the supervisor's correction as an agent message without user authority. One committer per mode keeps the commit rules in one place, and a focused Haiku prompt (git-ops) follows them reliably where a crowded one does not.
Rejected: curator and clerk committing their own writes.

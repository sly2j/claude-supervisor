---
domain: process
summary: A linked worktree's .supervisor/ is its branch's memory, landed by git; off the default branch store writers commit it
affects: [pack/skills/project-memory/SKILL.md, pack/skills/lead-loop/SKILL.md]
verified: 2026-10-22
source: user 2026-10-22, .supervisor/archive/working/plans/plan-store-persistence.md#decisions
supersedes: 
---
D1 (user, option a). A linked worktree's `.supervisor/` is its branch's memory and lands with the branch; git merges it, with no separate sync step. Off the default branch, whoever writes store files (a lead, `curator`, `clerk`, `writer`) ends its run with a pathspec commit of them, `chore(memory): <what>`, per `git-safety` Commits, with no `VERSION` change. Why: a planning-only session in a user-made worktree lost its plan because nothing committed it. Rejected: a memory sync step after landing (git already merges committed files).

Reach: product; stated in `pack/skills/project-memory/SKILL.md` (Committing the store) and `pack/skills/lead-loop/SKILL.md`.

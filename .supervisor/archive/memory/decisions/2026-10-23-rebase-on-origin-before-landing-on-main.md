---
domain: process
summary: Before any commit or merge into main, in any project, fetch and pull --rebase from origin; push to all remotes in one step, origin first
affects: [pack/skills/repo-workflow/SKILL.md, pack/agents/git-ops.md, pack/agents/executor.md, pack/skills/git-safety/]
verified: 2026-10-24
source: user 2026-10-23 ("we should always do a rebase pull from origin (in any context or any project) before commiting or merging anything into main"; approved the refinement: "yours is better, proceed")
supersedes:
superseded by: pack/skills/repo-workflow/SKILL.md (Sync With Origin); CLAUDE.md
---
Reach: product behaviour, written into `pack/` (`repo-workflow`, `git-ops`, executor landing) by executor in the same change set that lands this entry.

Decided (owner sjoosten):
- Before any commit or merge into the default branch (`main`), in any project: `git fetch origin`, then `git pull --rebase origin main`, so local unpushed commits sit on top of origin's. Applies to every agent that lands on main: executor as Mode 1 lead, git-ops for Mode 2 commits.
- With more than one remote, push to all remotes in the same step, origin first, so no remote holds a commit origin lacks. Rebasing is safe only while local commits are on no remote.

Why: on 2026-10-23 a commit was pushed to `public` before `origin`. Origin rejected it (three newer commits from another session); `public` already had it, so a rebase was ruled out and a conflicted merge commit (1879b49) was needed.

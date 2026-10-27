---
domain: process
summary: The store is committed in the branch and only curator creates it; one-off directories persist nothing
affects: [pack/skills/project-memory/, pack/skills/repo-workflow/SKILL.md, pack/skills/git-safety/references/conflict-resolution.md, pack/agents/curator.md, pack/agents/supervisor.md]
verified: 2026-10-27
source: user 2026-10-23 (commit ownership); .supervisor/archive/working/plans/plan-memory-v2.md#scope-notes (D1, D13); .supervisor/archive/working/plans/plan-store-persistence.md#decisions (D1-D7); user 2026-10-21 and 2026-10-22
supersedes: .supervisor/archive/memory/decisions/2026-10-23-store-lives-in-the-branch-2.md
---
Behaviour is in the pack (`project-memory`, `repo-workflow`, `git-safety`); this keeps the why and the rejections.
- Committed, not local: collaborators and later sessions share `.supervisor/` (a user who wants it local gitignores it). A worktree's store is its branch's memory and git merges it; a sync step after landing is rejected. A planning-only session lost its plan once.
- Default-branch commits stage pending store changes; git-ops commits, not curator (`2026-10-24-git-ops-not-curator-or-clerk-commits.md`). Risk: carrying a half-written file, so reports list the store paths.
- Conflicts keep both sides of `history.md` and plan Logs; an entry changed on both sides keeps the default-branch text.
- Only curator creates the store, idempotently, because deciders never saw the detection rule. Rejected: preloading `project-memory` into more agents (about 910 words of context).
- One-off directories persist nothing and ask nothing: `~/.claude/` made every directory under `~` a project, and ask-once flows cost more than they saved.

---
domain: process
summary: The store is tracked or local by the user's choice, committed in the branch when tracked; only curator creates it; one-off directories persist nothing
affects: [pack/skills/project-memory/, pack/skills/repo-workflow/SKILL.md, pack/skills/git-safety/references/conflict-resolution.md, pack/agents/curator.md, pack/agents/supervisor.md]
verified: 2026-10-29
source: user 2026-10-23 (commit ownership); user 2026-10-28 (tracked or local choice); .supervisor/archive/working/plans/plan-store-persistence.md#decisions; user 2026-10-21 and 2026-10-22
supersedes: .supervisor/archive/memory/decisions/2026-10-24-the-store-is-committed-in-the-branch-and.md
---
Behaviour is in the pack (`project-memory`, `repo-workflow`, `git-safety`); this keeps the why and the rejections.
- Tracked or local is the user's choice, asked once before a store is created in git. A tracked store is committed with its branch, so collaborators and later sessions share it; git merges a worktree's store as that branch's memory. Rejected: a sync step after landing. A planning-only session once lost its plan.
- Default-branch commits stage pending store changes; `git-ops` commits, not curator (`.supervisor/memory/decisions/2026-10-24-git-ops-not-curator-or-clerk-commits.md`).
- Conflicts keep both sides of `history.md` and plan Logs; an entry changed on both sides keeps the default-branch text.
- Only curator creates the store, idempotently, because deciders never saw the detection rule. Rejected: preloading `project-memory` into more agents.
- One-off directories persist nothing and ask nothing: `~/.claude/` made every directory under `~` a project.

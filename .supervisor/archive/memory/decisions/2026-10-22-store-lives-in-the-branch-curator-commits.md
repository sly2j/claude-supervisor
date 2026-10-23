---
domain: process
summary: The store is committed and lives in the branch; only curator creates it; why each commit and landing step carries pending store changes
affects: [pack/skills/project-memory/, pack/skills/repo-workflow/SKILL.md, pack/skills/git-safety/references/conflict-resolution.md, pack/agents/curator.md, pack/agents/supervisor.md]
verified: 2026-10-22
source: docs/archive/plan-memory-v2.md#scope-notes (D1, D13); .supervisor/archive/working/plans/plan-store-persistence.md#decisions (D1-D7); user 2026-10-21 and 2026-10-22
supersedes: [.supervisor/archive/memory/decisions/2026-10-21-project-memory-lives-in-supervisor-in.md, .supervisor/archive/memory/decisions/2026-10-22-worktree-store-is-the-branchs-memory.md, .supervisor/archive/memory/decisions/2026-10-22-only-curator-creates-the-store.md, .supervisor/archive/memory/decisions/2026-10-22-supervisor-makes-the-project-first.md, .supervisor/archive/memory/decisions/2026-10-22-one-off-persists-nothing-curator-stores.md, .supervisor/archive/memory/decisions/2026-10-22-every-commit-stages-pending-store.md, .supervisor/archive/memory/decisions/2026-10-22-landing-squash-carries-pending-store.md, .supervisor/archive/memory/decisions/2026-10-22-store-conflicts-keep-both-sides.md]
---
Behaviour is in the pack (`project-memory` Committing the store and Projects and one-offs,
`repo-workflow` Store changes and landing, `git-safety` conflict-resolution, `curator.md`,
`supervisor.md`); this keeps the why and the rejected options.

- Committed, not local: collaborators and later sessions share `.supervisor/`. A user who wants
  it local gitignores it and archive moves use plain `mv`. Consequences: no secrets or personal
  notes in entries; branches can diverge in memory state.
- A linked worktree's store is its branch's memory and git merges it; no sync step after landing
  (rejected). Trigger: a planning-only session in a user-made worktree lost its plan because
  nothing committed it. Off the default branch the writer commits its store files.
- On the default branch every commit also stages that checkout's pending store changes (except
  mid-conflict), which gives "the store is committed" an owner. Risk: a commit can carry another
  stage's half-written store file, so reports list the store paths committed. Rejected: one commit
  per default-branch store write (a `VERSION` bump per entry). Landing does the same into the
  squash commit; a `git merge --squash` refusal (for example an untracked store file the branch
  also adds) is fixed by committing the store first.
- Store conflicts: both sides of `history.md` and plan Logs are kept; an entry changed on both
  sides keeps the default-branch text and the report names the branch text with
  `follow-up: curator`. Never drop an entry file.
- Only `curator` creates the store, idempotently, because deciders never saw the detection rule
  and so nothing created or committed it. `supervisor` therefore dispatches `make this a project`
  before the session's first store-writing stage with no existence check. Rejected: preloading
  `project-memory` into more agents (about 910 words of context).
- One-off directories persist nothing and ask nothing (owner 2026-10-21): `~/.claude/` had made
  every directory under `~` a project, and the ask-once flow and its scratch markers, retention
  and promotion cost more than they saved. The root walk stops at the git toplevel and ignores
  `$HOME` and its ancestors, per worktree.

superseded by: .supervisor/memory/decisions/2026-10-23-store-lives-in-the-branch.md, .supervisor/memory/decisions/2026-10-23-only-git-ops-commits-memory-writes.md

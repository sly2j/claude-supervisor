---
summary: Let one worktree pick up several task cards, in sequence or in parallel
status: active
owner: feat/pick-up-several-cards-in-one-worktree
since: 2026-11-10
plan: .supervisor/working/plans/pick-up-several-cards-in-one-worktree.md
depends: []
decisions:
  - .supervisor/memory/decisions/2026-11-10-mid-term-work-is-task-cards-not-a-roadmap.md
  - .supervisor/memory/decisions/2026-11-10-a-picked-card-routes-as-a-typed-prompt.md
  - .supervisor/memory/decisions/2026-11-10-a-pushed-claim-is-advisory-not-a-lock.md
---
Goal: One worktree can pick up several cards, one after another or together under one plan.
Scope: Sequence: claims happen in the default-branch checkout before a worktree is cut, and no text covers claiming a second card from inside a worktree. `owner:` is the branch the work lands from. Parallel: `/pick-up` takes one argument and briefs one card, and no text lets one plan cover several cards. Close-out already finishes every live card whose `plan:` is the plan, each with its own `history.md` line.
Done when: `/pick-up` accepts several cards, one plan may cover them, a claim rule exists for a session already in a worktree, and the docs say so.
Notes: `supervisor.md` has no word headroom; the owner's simplicity rule applies. `<type>/<card slug>` is only a default branch name.

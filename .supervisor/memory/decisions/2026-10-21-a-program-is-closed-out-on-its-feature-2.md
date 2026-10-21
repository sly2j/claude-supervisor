---
domain: process
summary: A program is closed out on its feature branch before the squash merge, so the merge lands the store changes
affects: [CLAUDE.md, .supervisor/roadmap.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-memory-v2.md#open-questions
supersedes: .supervisor/archive/memory/decisions/2026-10-21-a-program-is-closed-out-on-its-feature.md
---
When a major program is developed on a feature branch, `curator close-out` of that program runs on the branch before the squash merge to `main`. The close-out writes the program's entries, removes the landed roadmap items, appends the `history.md` line and archives the plan; the owner reviews that diff and commits it on the branch, and the squash merge then carries everything to `main` as one commit with the `VERSION` bump. The history line names the version the squash commit will carry.

Why: `main` takes one commit per change set and every such commit must raise `VERSION` (CLAUDE.md). Rejected: closing out after the merge as its own change set (a "2.1"), which costs one more `main` commit and version bump and leaves `main` briefly describing landed work as still planned. Consequence: the close-out brief states the version in advance (`VERSION` on `main` plus one, or `X.0` for a major branch), and the store stays consistent at every commit on `main`. CLAUDE.md states the rebase and squash steps but not this one, so a session landing a branch must run the close-out first.

Reach: repo work.

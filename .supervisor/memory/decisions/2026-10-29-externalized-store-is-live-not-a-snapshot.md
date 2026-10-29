---
domain: process
summary: An externalized project store is one live directory reached by symlinks, never a snapshot copy
affects: [deploy, docs/local-memory.md, pack/skills/repo-workflow/references/external-store.md]
verified: 2026-10-29
source: .supervisor/archive/working/plans/externalize-memory.md
supersedes:
---
A project's memory kept outside its repo is the live store: `.supervisor` and `CLAUDE.local.md` are symlinks into one external directory, shared by every linked worktree. The user syncs that directory themselves; the pack never pushes or pulls it, and `git-ops` only commits inside it.
Why: a copy gives two stores that drift, and nothing merges a local store across worktrees.
Rejected: a snapshot or rsync backup (copies drift, residue is unfiltered, `--delete` overwrites on collision); a state file naming the root (the symlink already records it); per-worktree stores (lost or hand-merged).

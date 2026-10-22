---
domain: process
summary: Project memory lives in .supervisor/ in the repo and is committed
affects: [pack/skills/project-memory/]
verified: 2026-10-22
source: docs/archive/plan-memory-v2.md#scope-notes
supersedes: 
---
D1. The store is `.supervisor/` at the project root and is committed, so collaborators and later
sessions share it. A user who wants it local adds `.supervisor/` to `.gitignore`; archive moves then
use plain `mv`. Consequence: entries must hold no secrets or personal notes, and branches can
diverge in memory state (ROADMAP item "Memory across branches and worktrees").
superseded by: .supervisor/memory/decisions/2026-10-22-store-lives-in-the-branch-curator-commits.md

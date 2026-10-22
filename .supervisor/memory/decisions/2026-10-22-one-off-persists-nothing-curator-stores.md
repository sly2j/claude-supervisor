---
domain: process
summary: One-off directories persist nothing and ask nothing; root bounded by git and $HOME, per worktree; only curator creates the store
affects: [pack/skills/project-memory/, pack/agents/curator.md, pack/agents/clerk.md]
verified: 2026-10-22
source: docs/archive/plan-memory-v2.md#scope-notes; .supervisor/archive/working/plans/plan-store-persistence.md#decisions
supersedes: .supervisor/archive/memory/decisions/2026-10-21-one-off-directories-persist-nothing-and.md
---
D13 (owner, 2026-10-21), restated after the store-persistence change (that plan's D5 and D7). A project is a git work tree, or a directory with `.supervisor/`, `.claude/`, `CLAUDE.md` or `AGENTS.md` here or above, never counting `$HOME` or its ancestors; the walk stops at the git toplevel. Inside a git work tree the root is the nearest `.supervisor/` within it, else the git toplevel, which wins over anything above; in a linked worktree that is the worktree's own, so each worktree has its branch's store. Outside git it is the nearest `.supervisor/`, else the nearest other signal. The marker set is unchanged. A one-off directory persists nothing and asks nothing: an agent that would have stored something reports exactly `not stored: no project store here; say *remember* to keep it`. Only `curator` creates the store, and commits it (`.supervisor/memory/decisions/2026-10-22-only-curator-creates-the-store.md`), on `remember`, `make this a project` or a close-out, in the current directory (never `$HOME`). Scratch markers, `$CLAUDE_CONFIG_DIR/scratch`, retention and promotion are removed. Why: `~/.claude/` made every directory under `~` a project, and the ask-once flow cost more than it saved.

---
domain: process
summary: One-off directories persist nothing and ask nothing; project root bounded by git and $HOME
affects: [pack/skills/project-memory/, pack/agents/curator.md, pack/agents/clerk.md]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#scope-notes
supersedes: .supervisor/archive/memory/decisions/2026-10-21-work-areas-get-supervisor-only-when-long.md
---
D13 (owner, 2026-10-21, after V3 step 6). A project is a git work tree, or a directory with
`.supervisor/`, `.claude/`, `CLAUDE.md` or `AGENTS.md` here or above, never counting `$HOME` or its
ancestors; the walk stops at the git toplevel. Inside a git work tree the root is the nearest
`.supervisor/` within it, else the git toplevel, which wins over anything above it; outside git it
is the nearest `.supervisor/`, else the nearest other signal. A one-off directory persists nothing
and asks nothing: an agent that would have stored something reports exactly `not stored: no project
store here; say *remember* to keep it`. Only `remember`, `make this a project` or a close-out
creates the store, in the current directory (never `$HOME`). Scratch markers,
`$CLAUDE_CONFIG_DIR/scratch`, retention and promotion are removed. Why: `~/.claude/` made every
directory under `~` a project, and the ask-once flow cost more than it saved.

superseded by: .supervisor/memory/decisions/2026-10-22-one-off-persists-nothing-curator-stores.md

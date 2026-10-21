---
domain: process
summary: Work areas get .supervisor/ only when long-term; one-offs use scratch and ask once
affects: [pack/skills/project-memory/]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#open-questions
supersedes: 
superseded by: .supervisor/memory/decisions/2026-10-21-one-off-directories-persist-nothing-and.md
---
D12 (the owner's default, OQ3). Create `.supervisor/` automatically only in a clearly long-term
work area (git repo, `CLAUDE.md` or `.claude/`, `.obsidian/`, existing `.supervisor/`, or the user
says so). A clear one-off job gets scratch only, under `$CLAUDE_CONFIG_DIR/scratch/<key>/`, pruned
after 30 days without file changes; ambiguous areas ask once whether the directory is a long-term
work area, the answer persisting in a marker file. Staleness falls back to mtime without git.
Replaced by D13 after V3: the scratch machinery proved heavy and `~/.claude/` made every directory
under `~` look like a project.

---
domain: process
summary: Memory work was developed on a feature branch and worktree under a dev tag
affects: [docs/deploy.md]
verified: 2026-10-22
source: ROADMAP.md item 1, 2026-10-21
supersedes: 
---
Development of the memory system happened on the branch `memory-v2` in a separate git worktree,
deployed as `claude-supervisor-dev`, so the stable sandbox stayed untouched and designs not ready
for general users could change freely. Feature branches never touch `VERSION`; the squash-merge
commit sets it (CLAUDE.md). The flow is documented in `docs/deploy.md`.
dropped: 2026-10-22 (memory audit: covered by pack/, CLAUDE.md or docs, or no longer a live claim)

---
domain: process
summary: Agent names are roles; quick-edit became clerk, git-ops and curator keep theirs
affects: [pack/agents/clerk.md, pack/agents/git-ops.md, pack/agents/curator.md, docs/architecture.md]
verified: 2026-10-21
source: ROADMAP.md item 1, 2026-10-21
supersedes: 
---
Agent names are roles. Stage 1 renamed `quick-edit` to `clerk` because the agent now records
memory entries and log lines as well as small edits; `git-ops` keeps its name; the memory agent is
`curator`. `deploy` removes the old managed `quick-edit.md` on upgrade unless edited locally.

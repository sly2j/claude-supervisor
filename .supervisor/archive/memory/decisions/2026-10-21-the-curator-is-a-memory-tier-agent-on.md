---
domain: process
summary: The curator is a Memory-tier agent on sonnet, default effort (high until 2.11), body cap 400, no Agent tool
affects: [pack/agents/curator.md, pack/skills/agent-authoring/SKILL.md, tests/test_pack_lint.py]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#approach
supersedes: 
---
A new `Memory` tier row (`sonnet / high`, body cap 400, explicit tool allowlist, no Agent), the
supervisor dispatching the curator at depth 1. Rejected: curator in the Worker row (Worker means
lead-dispatched at depth 2) and a Mode 2 table row for it (about ten supervisor words; the Programs
clause routes it).
dropped: 2026-10-22 (memory audit: covered by pack/, CLAUDE.md or docs, or no longer a live claim)

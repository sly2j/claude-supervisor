---
domain: process
summary: Idle plans (30 days without Log activity) are proposed for archiving, never archived automatically
affects: [pack/skills/project-memory/references/curator-procedures.md, pack/agents/curator.md]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#approach
supersedes: 
---
On every run the curator lists plans whose last `## Log` line is over 30 days old (last commit date
when the log is empty) and asks archive-or-keep. Archive is a `curator close-out` of an unfinished
plan (no roadmap step, no goal marked met); keep is a `clerk` brief appending `user: kept active`,
which resets the clock. The sweep never moves a file; a false positive costs one question.
dropped: 2026-10-22 (memory audit: covered by pack/, CLAUDE.md or docs, or no longer a live claim)

---
domain: process
summary: Expiry flags an entry when its affects paths change; no time-based archiving
affects: [pack/skills/project-memory/]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#open-questions
supersedes: 
---
D6 (OQ1, default accepted by the user 2026-10-18). An entry is a claim to re-check when an
`affects:` path is missing or changed since `verified:` (`git log --since`, file mtime without git).
No time-based archiving of entries in v2.0; revisit for `fact` entries only if staleness is
observed. The curator re-verifies or supersedes flagged entries at close-out.

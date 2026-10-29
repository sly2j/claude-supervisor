---
domain: process
summary: tools/audit/ is opt-in tooling: never run by default, lightly documented, outputs never committed
affects: [tools/audit/]
verified: 2026-10-29
source: user 2026-10-24 (owner decision after .supervisor/archive/working/research/research-fold-subagents.md)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-efficiency-scripts-are-opt-in-tooling.md
---
The audit scripts live in the repo to re-measure efficiency drift against the baseline fact (`.supervisor/memory/facts/2026-10-24-efficiency-baseline-for-drift.md`).
Why: transcripts contain other projects' content, so outputs must never be committed and nothing runs by default; light documentation keeps the tool out of normal workflows.

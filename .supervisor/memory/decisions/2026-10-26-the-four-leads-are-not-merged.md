---
domain: process
summary: Keep supervisor, leads, workers and the Haiku quick tier as separate agents; the four leads are not planned to merge
affects: [pack/agents/, docs/architecture.md]
verified: 2026-10-29
source: user 2026-10-26 (owner ruling; earlier owner decision followed .supervisor/archive/working/research/research-fold-subagents.md)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-keep-supervisor-leads-workers-and-the-ha.md
---
Keep the architecture. Scout and fixer absorb large reads (fixer also maintains plan state in programs), curator keeps memory reads out of the main thread, and each lead holds its domain's harness. The four leads are quite different, so no merge is planned; it was considered briefly and decided against.
Why: the audit measured main-loop bloat and parallel discardable context (see `.supervisor/memory/facts/2026-10-24-efficiency-baseline-for-drift.md`), and the use case is long-horizon multi-session work.
Rejected: a full single-loop fold; folding the Haiku tier into the supervisor; dropping the supervisor's no-read rule; merging the four leads.

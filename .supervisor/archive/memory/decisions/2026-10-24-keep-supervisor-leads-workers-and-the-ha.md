---
domain: process
summary: Keep supervisor, leads, workers and the Haiku quick tier as separate agents; do not fold into one loop
affects: [pack/agents/, docs/architecture.md]
verified: 2026-10-24
source: user 2026-10-24 (owner decision after .supervisor/archive/working/research/research-fold-subagents.md)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-multi-agent-architecture-stays.md
---
Keep the architecture. Scout and fixer absorb large reads (fixer also maintains plan state in programs), curator keeps memory reads out of the main thread, and each lead holds its domain's harness.
Why: the claim that Anthropic's guidance accepts subagents only for measured main-loop bloat or parallel discardable context is met here: the audit measured both (see `.supervisor/memory/facts/2026-10-24-efficiency-baseline-for-drift.md`), and the use case is long-horizon multi-session work.
Rejected: a full single-loop fold; folding the Haiku tier into the supervisor; dropping the supervisor's no-read rule; merging the four leads before efficiency is measured (revisit only with measurements).
superseded by: .supervisor/memory/decisions/2026-10-26-the-four-leads-are-not-merged.md

---
domain: process
summary: Keep supervisor, leads, workers and the Haiku quick tier as separate agents, answering the claim that subagents are justified only by measured main-loop bloat or parallel discardable context
affects: [pack/agents/, docs/architecture.md]
verified: 2026-10-24
source: user 2026-10-24 (owner decision after .supervisor/archive/working/research/research-fold-subagents.md)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-keep-the-multi-agent-architecture.md
---
Keep the architecture; do not fold into one loop. Scout and clerk absorb large reads (clerk also maintains plan state in programs), curator keeps memory reads out of the main thread, and each lead holds its domain's harness.
Answers the claim "Anthropic's guidance accepts subagents only for measured main-loop bloat or parallel discardable context". The audit measured both (85% of tokens in subagents, main-thread median final context 66k, nesting at most 2, the supervisor's no-read rule holds), and the use case is long-horizon multi-session work.
Rejected: a full single-loop fold; folding the Haiku tier into the supervisor; dropping the supervisor's no-read rule; merging the four leads before efficiency is measured (revisit only with measurements).

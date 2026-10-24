---
domain: process
summary: keep supervisor + leads + workers + Haiku quick tier, and scout, clerk, curator and the four leads as separate agents, against the article's single-loop default
affects: [pack/agents/, docs/architecture.md]
verified: 2026-10-24
source: user 2026-10-24 (owner decision after .supervisor/working/research/research-fold-subagents.md)
supersedes:
superseded by: .supervisor/memory/decisions/2026-10-24-multi-agent-architecture-stays.md
---
Keep the architecture; do not fold into one loop. Scout and clerk absorb large reads (clerk also maintains plan state in programs), curator keeps memory reads out of the main thread, and each lead holds its domain's harness.
Why: Anthropic's 2026-10-22 article accepts subagents for measured main-loop bloat and for parallel work with discardable context; the audit measured both (85% of tokens in subagents, main-thread median final context 66k, nesting <= 2, supervisor no-read rule holds), and the use case is long-horizon multi-session work.
Rejected: a full single-loop fold; folding the Haiku tier into the supervisor; dropping the supervisor's no-read rule; merging the four leads before efficiency is measured (revisit only with measurements).

---
domain: process
summary: efficiency baseline 2026-10-24 (27 sessions, 816 subagent transcripts, 89 lead runs) for drift monitoring
affects: [pack/skills/lead-loop/SKILL.md, pack/agents/]
verified: 2026-10-29
source: .supervisor/archive/working/research/research-fold-subagents.md
supersedes:
---
Corpus: 27 sessions, 816 subagent transcripts, 89 lead runs over about 10 days, pack versions mixed (indicative, not stable).
- Round-1 critic PASS: executor 44/52, researcher 4/12, planner 7/15; rounds 2 and later 91% (45/49).
- Executor tree 339M of 619M lead-tree tokens; 38 files re-read by several workers (30 under executor).
- Quick tier: 5/165 ESCALATE, about 24M Haiku tokens. Main thread median final context 66k; subagents 85% of tokens.

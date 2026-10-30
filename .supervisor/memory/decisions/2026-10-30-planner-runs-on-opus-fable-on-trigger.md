---
domain: process
summary: Planner runs on Opus by default; supervisor passes Fable per dispatch for programs, open cross-module design or large domains
affects: [pack/agents/planner.md, pack/agents/supervisor.md, pack/skills/agent-authoring/SKILL.md, docs/architecture.md]
verified: 2026-10-30
source: user 2026-10-30
supersedes:
---
The planner lead is a cheaper default with a Fable escalation, like the executor. The critic follows the planning tier: Fable only when the brief carries the tier line, else its default Opus. Annotation cycles and checklist sync never escalate.
Why: the usage panel's advice to move planner to Opus rests on spend share alone, with no quality signal. Fable costs 2.5x Opus per token ($10/$50 vs $4/$20 per MTok), and a planning run put planner, critic and scope-critic all on Fable. The approval gate already catches a weak Opus plan before execution, and re-planning on Fable is cheap.
Rejected: a live A/B of past plans on Opus vs Fable (real cost, tiny sample, subjective quality); staying on Fable.
Related: `.supervisor/memory/decisions/2026-10-27-executor-runs-on-sonnet-by-default.md`.
---

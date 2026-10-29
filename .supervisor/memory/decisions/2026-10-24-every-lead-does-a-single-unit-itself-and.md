---
domain: process
summary: Every lead does a single unit itself and dispatches workers only for two or more independent units or heavy raw inputs
affects: [pack/skills/lead-loop/SKILL.md, pack/agents/supervisor.md, pack/agents/executor.md, pack/agents/researcher.md, pack/agents/planner.md, pack/agents/writer.md, pack/agents/scope-critic.md, docs/architecture.md, tools/audit/audit.py]
verified: 2026-10-29
source: user 2026-10-24 (owner decisions after .supervisor/archive/working/research/research-fold-subagents.md and .supervisor/archive/working/plans/plan-fold-subagents.md)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-every-lead-does-a-single-unit-itself.md
---
Every lead (researcher, planner, executor, writer) does a single unit itself; workers take two or more independent units, or one whose raw inputs would crowd out the lead's review loop. Writer source extraction stays with workers. `Path: minimal` is the Mode 1 shortcut for every lead. Scope-critic is skipped when the critic's table has no row above NIT and the size bound holds.
Why: files were re-read by several workers, and the lead reads the draft anyway to judge critic findings, so delegating a single unit saved no context. The skip rule is loosened from "no findings" because only 4 of 52 executor first-round tables were empty.
Rejected: a single-worker exception for researcher and writer; it split the voice and saved nothing.
Writer data is thin (14 lead runs); re-measure with `tools/audit/audit.py` before tuning the size bound.

---
domain: process
summary: the next major folds within the harness; scope-critic is skipped on a critic round with no findings above NIT, measured at 4/52 empty tables
affects: [pack/skills/lead-loop/SKILL.md, pack/agents/supervisor.md, pack/agents/executor.md, pack/agents/scope-critic.md, docs/architecture.md, tools/audit/audit.py]
verified: 2026-10-24
source: user 2026-10-24 (owner decisions after .supervisor/working/research/research-fold-subagents.md and .supervisor/working/plans/plan-fold-subagents.md)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-next-major-folds-within-the-harness.md
superseded by: .supervisor/memory/decisions/2026-10-24-uniform-single-unit-rule-for-all-leads.md
---
The next major version carries three changes (number set by the squash commit at landing; another branch also heads for a major, so do not hard-code it): R2 skip scope-critic, R3 the executor lead does a single unit itself, R4 a named `Path: minimal` Mode 1 path.
R2 condition: skip scope-critic when the critic's findings table has no row above NIT (BLOCKING, MUST, SHOULD) and the size bound holds. Owner loosened it from "no findings" because the audit tool showed only 4/52 executor round-1 reports had an empty table, so the strict rule would almost never skip.
Measured skip-eligible first rounds under the loosened rule: executor 15/56, writer 3/14, researcher 1/15, planner 1/17. The earlier "unmeasured" claim is settled; re-measure with `tools/audit/audit.py` before tuning the size bound.
Why for R3/R4: 38 files were re-read by several workers (30 under executor). Researcher and writer keep their single-worker defaults (raw sources and drafts stay out of the lead's context).

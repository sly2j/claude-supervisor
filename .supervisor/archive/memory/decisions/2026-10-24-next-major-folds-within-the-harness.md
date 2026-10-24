---
domain: process
summary: the next major version (X.0) folds within the harness - scope-critic skipped on a clean critic, executor lead does a single unit itself, named minimal Mode 1 path
affects: [pack/skills/lead-loop/SKILL.md, pack/agents/supervisor.md, pack/agents/executor.md, pack/agents/scope-critic.md, docs/architecture.md]
verified: 2026-10-24
source: user 2026-10-24 (owner decision after .supervisor/working/research/research-fold-subagents.md, R2-R4)
supersedes:
---
The next major version carries three changes; the planner settles the details. Its number is set by the squash commit at landing (another branch is also heading for a major, so it may be 6.0 or 7.0); do not hard-code it.
- R2: skip scope-critic when critic returns no findings, with a cheap bloat check or size condition.
- R3: the executor lead implements a single unit itself and fans out only for several disjoint units, as planner already writes to itself.
- R4: name a minimal Mode 1 path (one lead, no fan-out, one critic pass) that the supervisor can brief deliberately.
Why: the audit showed round-1 critic PASS in 44/52 executor runs and 38 files re-read by several workers (30 under executor). The scope-critic claim (it adds little after a clean PASS) is unmeasured, so the planner should state the check.

superseded by: .supervisor/memory/decisions/2026-10-24-scope-critic-skips-on-nit-only-rounds.md

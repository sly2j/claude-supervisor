---
domain: process
summary: every lead does a single unit itself and dispatches workers only for two or more independent units or heavy raw inputs; scope-critic skips on NIT-only rounds; Path: minimal
affects: [pack/skills/lead-loop/SKILL.md, pack/agents/supervisor.md, pack/agents/executor.md, pack/agents/researcher.md, pack/agents/planner.md, pack/agents/writer.md, pack/agents/scope-critic.md, docs/architecture.md, tools/audit/audit.py]
verified: 2026-10-24
source: user 2026-10-24 (owner decisions after .supervisor/working/research/research-fold-subagents.md and .supervisor/working/plans/plan-fold-subagents.md; uniform rule added the same day)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-scope-critic-skips-on-nit-only-rounds.md
superseded by: .supervisor/memory/decisions/2026-10-24-every-lead-does-a-single-unit-itself.md
---
The next major version carries three changes (number set by the squash commit at landing; another branch also heads for a major, so do not hard-code it): R2 skip scope-critic, R3 a lead does a single unit itself, R4 a named `Path: minimal` Mode 1 path.
R2 condition: skip scope-critic when the critic's findings table has no row above NIT (BLOCKING, MUST, SHOULD) and the size bound holds. Owner loosened it from "no findings" because the audit tool showed only 4/52 executor round-1 reports had an empty table, so the strict rule would almost never skip.
Measured skip-eligible first rounds under the loosened rule: executor 15/56, writer 3/14, researcher 1/15, planner 1/17. Re-measure with `tools/audit/audit.py` before tuning the size bound.
R3 is uniform across researcher, planner, executor and writer: a lead does a single unit itself and dispatches workers only for two or more independent units, or when one unit's raw inputs are heavy enough to crowd out the lead's own review loop. Writer: source extraction stays with workers, drafting and revision move to the lead. Researcher: a single bounded question is done by the lead, workers for several questions or a large raw corpus. `Path: minimal` thereby reaches every lead.
Why R3: 38 files were re-read by several workers (30 under executor). Rejected: the researcher/writer single-worker exception from the first fold decision ("keep drafts out of the lead's context"); the lead must read the draft to integrate and judge critic findings anyway, so delegating drafting saved no context and split the voice.
Unmeasured: only 14 writer lead runs in the corpus. The audit tool gains a lead-final-context-size metric so roadmap item 8 can check for bloat in self-drafting leads. Related: `keep-the-multi-agent-architecture` (agents stay separate; this changes who does a single unit, not the roster).

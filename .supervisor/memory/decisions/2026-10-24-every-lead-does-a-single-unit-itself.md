---
domain: process
summary: Every lead does a single unit itself and dispatches workers only for two or more independent units or heavy raw inputs; scope-critic skips when no finding is above NIT; Path: minimal is the Mode 1 shortcut
affects: [pack/skills/lead-loop/SKILL.md, pack/agents/supervisor.md, pack/agents/executor.md, pack/agents/researcher.md, pack/agents/planner.md, pack/agents/writer.md, pack/agents/scope-critic.md, docs/architecture.md, tools/audit/audit.py]
verified: 2026-10-24
source: user 2026-10-24 (owner decisions after .supervisor/archive/working/research/research-fold-subagents.md and .supervisor/archive/working/plans/plan-fold-subagents.md)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-uniform-single-unit-rule-for-all-leads.md
---
Every lead (researcher, planner, executor, writer) does a single unit itself and dispatches workers only for two or more independent units, or when one unit's raw inputs are heavy enough to crowd out the lead's own review loop. Writer: source extraction stays with workers; drafting and revision are the lead's. Researcher: one bounded question is the lead's; workers take several questions or a large raw corpus. `Path: minimal` is the named Mode 1 shortcut and so reaches every lead.
Scope-critic is skipped when the critic's findings table has no row above NIT (BLOCKING, MUST, SHOULD) and the size bound holds. The owner loosened this from "no findings": only 4 of 52 executor round-1 reports had an empty table, so the strict rule would almost never skip. Measured skip-eligible first rounds under the loosened rule: executor 15/56, writer 3/14, researcher 1/15, planner 1/17.
Why: 38 files were re-read by several workers (30 under executor), and the lead reads the draft anyway to integrate and judge critic findings, so delegating a single unit saved no context.
Rejected: a researcher/writer single-worker exception to keep drafts out of the lead's context; it split the voice and saved nothing.
Unmeasured: only 14 writer lead runs in the corpus. Re-measure with `tools/audit/audit.py` (including the lead-final-context metric) before tuning the size bound or judging bloat in self-drafting leads. Related: `2026-10-24-multi-agent-architecture-stays.md` (the roster is unchanged; only who does a single unit moved).

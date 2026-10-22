---
domain: process
summary: The plan format lives in the plan-writing skill: decisions plus a signature-level outline, vertical slices, no implementation code, plan never longer than the change
affects: [pack/skills/plan-writing/SKILL.md, pack/agents/planner.md, pack/agents/critic.md, pack/agents/executor.md, pack/agents/executor-worker.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-planner-lighter-plans.md#decisions
supersedes:
---
Owner-approved 2026-10-21 (D1-D5, D7-D10 of the plan). Every rule the critic reviews plans against lives in `pack/skills/plan-writing/SKILL.md`; `planner.md` keeps workflow only (fan-out, questions first, review, annotation, report). A skill was chosen over trimming because the capped planner and critic files had no headroom.

Every plan, child plans included, has `## Goal` (with non-goals and expected change size), `## Approach`, `## Decisions` (mandatory), `## Outline`, `## Slices` (replaces `## Orchestration`), `## Verification`, `## Risks`, `## Scope Notes`, `## Assumptions`, `## Work Packages` when split, `## Open Questions`, `## Log`, `## Todo`. Rules: no implementation code (snippets only for non-obvious logic, at most 15 lines, marked illustrative; tests are a name plus assertion); slices are vertical, each with test cases and a checkpoint command, never by layer; a plan is never longer than the change it describes; a decision belongs in `## Decisions` or `## Open Questions`, never `## Assumptions`. `executor` runs each slice as a wave and runs its checkpoint before the next; a worker brief's excerpt is the slice's signatures, `file:line` pointers and test cases. `critic` loads the skill's reviewing section for domain `plan`. No new lint test: existing lint covers the skill.

Reach: product; written into pack/skills/plan-writing/SKILL.md and the agents that consume it.

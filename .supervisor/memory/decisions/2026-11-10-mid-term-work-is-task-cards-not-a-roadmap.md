---
domain: process
summary: Mid-term work is task cards in .supervisor/tasks/, one file per item; the single ordered roadmap file is gone
affects: [pack/skills/project-memory/references/tasks.md, pack/skills/pick-up/SKILL.md]
verified: 2026-11-10
source: .supervisor/archive/working/plans/plan-task-cards.md (user 2026-11-10)
supersedes: .supervisor/archive/memory/decisions/2026-10-24-the-roadmap-stays-at-supervisor-roadmap.md
---
A task is a card file that carries its own owner and coarse status; ordering comes from `depends:` only, with no priority field.
Why: one ordered file cannot show who has an item or what blocks it, and several sessions or clones need to claim work.
Rejected: card rules inline in `SKILL.md` (over the word cap), a pickup rule in `supervisor.md` (a rule cut is owner-only), a `task` agent or skill (no observed need), a pytest lint of store content.

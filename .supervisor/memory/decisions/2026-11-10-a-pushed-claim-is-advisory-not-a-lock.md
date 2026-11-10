---
domain: process
summary: A task claim is an advisory marker, not a cross-clone lock; pushed claims as a lock and auto-release of stale claims were not adopted
affects: [pack/skills/project-memory/references/tasks.md]
verified: 2026-11-10
source: .supervisor/archive/working/plans/plan-task-cards.md (user 2026-11-10)
supersedes:
---
A claim is a status edit committed as `chore(memory): claim <card>`; it shows to other clones once pushed and guards nothing beyond that.
Why: a real lock needs a push before work starts and a release rule, which costs more than the occasional duplicate pickup.
Rejected: pushing claims as a lock; releasing stale claims automatically (the audit only flags them).

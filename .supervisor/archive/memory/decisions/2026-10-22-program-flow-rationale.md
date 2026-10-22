---
domain: process
summary: Program flow rationale: planner judges splits, one parent approval, questions first, waves with the plan as only state; close out on the feature branch
affects: [pack/agents/planner.md, pack/agents/supervisor.md, pack/skills/plan-writing/SKILL.md, docs/architecture.md, CLAUDE.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-wbs.md; .supervisor/archive/working/plans/plan-planner-lighter-plans.md; .supervisor/archive/working/plans/plan-memory-v2.md; owner 2026-10-21
supersedes: [.supervisor/archive/memory/decisions/2026-10-21-planner-decides-when-to-split-into.md, .supervisor/archive/memory/decisions/2026-10-21-planner-asks-questions-first-only-when-the.md, .supervisor/archive/memory/decisions/2026-10-21-the-supervisor-runs-work-packages-as-a.md, .supervisor/archive/memory/decisions/2026-10-21-a-program-is-closed-out-on-its-feature-2.md]
superseded by: .supervisor/memory/decisions/2026-10-22-supervisor-runs-packages-in-waves.md, .supervisor/memory/decisions/2026-10-22-close-out-a-program-on-its-branch.md
---
Behaviour is in `pack/agents/planner.md` (`## Work Packages`, `## Questions First`),
`pack/agents/supervisor.md` and `docs/architecture.md`; this keeps the why and rejected options.

- Splitting into packages is planner judgment; the user approves the parent plan once. A second
  approval round per split would stall long programs on bookkeeping already approved in outline.
- Questions first only when the brief leaves an open question or design fork. Rejected: one pass with
  questions left open; the planner asking the user directly (bypasses the supervisor's single user
  channel); a design stage in the package block (reopens the six-field decision).
- The supervisor runs packages in waves with the parent plan file as the only state, so a fresh
  session resumes from it; it never reads the plan and one writer at a time touches it. Rejected: a
  coordinator agent (the owner decided supervisor owns the loop); continuous per-return advancement
  (unbounded report cadence, harder resume); a `program-loop` skill (fits in a few bullets); the
  planner syncing status per transition (an expensive model for a one-line edit); the supervisor
  editing plans itself (all project changes go through agents).
- Repo work: a major program developed on a feature branch is closed out with `curator close-out` on
  the branch before the squash merge, so the merge lands the store changes in the one `main` commit
  with its `VERSION` bump; the close-out brief states the version in advance (`VERSION` on `main`
  plus one, or `X.0`). Rejected: closing out after the merge as its own change set, which costs a
  commit and bump and leaves `main` describing landed work as planned. CLAUDE.md does not state this
  step, so a session landing a branch must run the close-out first.

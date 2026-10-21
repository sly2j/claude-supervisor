---
domain: process
summary: Planner decides when to split into packages and the user approves the parent plan once
affects: [pack/agents/planner.md, pack/agents/supervisor.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-wbs.md#scope-notes
supersedes:
---
Whether work becomes packages is `planner` judgment: independent packages run in parallel by default, `Deps` are real inputs only, and plain parallel execution stays a flat plan. The user can force either form. The user approves the parent plan once and sees child plans only on a real design choice; packages added later by `Amend parent:` run without a further approval round.

Why: a second approval round for every split would stall long programs on bookkeeping the user already approved in outline.

`pack/agents/planner.md` (`## Work Packages`) states the judgment criterion, the parallel preference, the user override, the single parent approval and the no-approval rule for amended packages.

Reach: product; written into pack/agents/planner.md (## Work Packages), except "sees child plans only on a real design choice", which is NOT stated in the product.

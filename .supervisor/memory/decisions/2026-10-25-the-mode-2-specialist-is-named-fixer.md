---
domain: process
summary: The Mode 2 specialist is named fixer, not clerk or chore
affects: [pack/agents/fixer.md, pack/agents/supervisor.md, docs/architecture.md, tests/test_pack_lint.py]
verified: 2026-10-25
source: user 2026-10-25
supersedes:
---
The Mode 2 specialist formerly called `clerk` is named `fixer`.
Why: the user wanted a livelier name; `fixer` keeps the actor-noun pattern of the other agents and the small hands-on-jobs flavour.
Rejected: `chore` (collides with the conventional-commit type used in commits, making briefs and grep ambiguous; names the work, not the worker); `handyman` and `janitor` (not chosen); keeping `clerk`.
The older decision entry `2026-10-24-git-ops-not-curator-or-clerk-commits.md` keeps its file name on purpose, so links to it hold.

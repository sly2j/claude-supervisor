---
domain: process
summary: VERSION is bumped by hand as one line; no git tags, releases or hooks, and branches never bump it
affects: [VERSION, CLAUDE.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-versioning.md#scope-notes
supersedes:
---
The pack version is a one-line `VERSION` file at the repo root (`X.y`, `y` unbounded), raised by hand by whoever edits the files on `main`. The bump and branch-landing rules are in `CLAUDE.md`; this entry records the owner's decisions around them that the file does not state: no git tags, no changelog or release process, no CI or git hooks for versioning, and the rule applies to this repo only (deployed projects are untouched).

Why branches never bump: a branch-agnostic rule was tried on paper and rejected by the owner, because branches that bump produce duplicate numbers and merge conflicts on the one-line file. Branch work is instead versioned by deriving a label from git at install time (`<VERSION at merge-base with main>+<branch>.<ahead>.g<sha>`, see `docs/deploy.md`), which needs no edit and survives a rebase. A stray branch bump surfaces as a one-line conflict on `VERSION`, which `git-ops` already treats as mechanical.

Reach: repo work.

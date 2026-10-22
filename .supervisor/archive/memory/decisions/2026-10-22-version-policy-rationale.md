---
domain: process
summary: Version policy rationale: hand-bumped one-line VERSION, no tags or hooks, branches never bump, HEAD-only test on main
affects: [VERSION, CLAUDE.md, tests/test_version.py, docs/deploy.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-versioning.md
supersedes: [.supervisor/archive/memory/decisions/2026-10-21-version-is-bumped-by-hand-one-line-no.md, .supervisor/archive/memory/decisions/2026-10-21-the-version-bump-is-enforced-by-a-test.md]
superseded by: .supervisor/memory/decisions/2026-10-22-no-version-tags-hooks-or-release-process.md
---
The rules are in `CLAUDE.md` and `tests/test_version.py`; this keeps the owner's choices and why.
Repo work only; deployed projects are untouched.

- `VERSION` is a one-line file raised by hand. No git tags, changelog or release process, and no
  CI or git hooks for versioning.
- Branches never bump: a branch-agnostic rule was tried on paper and rejected by the owner, since
  bumping branches produce duplicate numbers and conflicts on the one-line file. Branch work gets a
  label derived from git at install time instead (see `docs/deploy.md`), which needs no edit and
  survives a rebase. A stray branch bump shows as a one-line `VERSION` conflict that `git-ops`
  treats as mechanical.
- Enforcement compares the working tree with `HEAD` only, on `main` only (skips elsewhere or when
  git state is missing): it works offline and right after a push, touches no remote refs or hooks,
  and checks what the next commit will contain. A dirty `main` without a bump failing is the
  intended reminder, not a flake; a squash merge counts as a dirty tree until its commit. The
  rule is a pure function (`bump_ok`) so it is testable without git.
- Rejected: a tracked pre-commit hook (inactive without `core.hooksPath` in every clone); comparing
  with `origin/main` (needs a fetched ref, fails right after a push); putting the rule in the
  `git-safety` skill (it ships to every project; this rule is specific to this repo).

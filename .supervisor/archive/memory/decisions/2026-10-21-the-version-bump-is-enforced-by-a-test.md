---
domain: process
summary: The VERSION bump is enforced by a HEAD-based test that runs on main only, not by a git hook or an origin/main check
affects: [tests/test_version.py, VERSION, CLAUDE.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-versioning.md#approach
supersedes:
---
`tests/test_version.py` fails on `main` when tracked files differ from `HEAD` and the working-tree `VERSION` is not strictly greater than `HEAD:VERSION`. It skips with a stated reason on any other branch, on a detached `HEAD`, and when git, `HEAD` or `HEAD:VERSION` is unavailable. The bump rule itself (`bump_ok`) is a pure function tested on its own cases, so the rule is testable without git state. The rule text for editing agents is in `CLAUDE.md`; this entry records why the enforcement has this shape.

Why it needs only `HEAD`: it works offline and right after a push, never touches remote refs or hooks, and reads only the working tree, which is what the next commit will contain. A clean `main` passes trivially; untracked files are ignored, so scratch files never trigger it. A dirty `main` without a bump failing is the intended reminder, not a flake, and a squash merge counts as a dirty tree until its commit.

Rejected: a tracked pre-commit hook (inactive without `core.hooksPath` in every clone, and per-clone setup is the fragile part); comparing against `origin/main` (needs a fetched remote ref and fails right after a push); putting the rule in the `git-safety` skill (that skill ships to every project, the rule is specific to this repo, so it stays in `CLAUDE.md`).

Reach: repo work.
superseded by: .supervisor/memory/decisions/2026-10-22-version-policy-rationale.md

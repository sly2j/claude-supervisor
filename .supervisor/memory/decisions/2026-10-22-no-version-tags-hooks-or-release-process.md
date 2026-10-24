---
domain: code
summary: Versioning is a hand-bumped VERSION file with no tags, changelog, release process, CI or hooks
affects: [VERSION, CLAUDE.md, tests/test_version.py]
verified: 2026-10-24
source: .supervisor/archive/working/plans/plan-versioning.md; owner 2026-10-21
supersedes: .supervisor/archive/memory/decisions/2026-10-22-version-policy-rationale.md
---
Repo work only; deployed projects are untouched.
Why: the owner wants nothing beyond the one-line file and its test. Rejected: a tracked pre-commit hook (inactive without `core.hooksPath` in every clone).

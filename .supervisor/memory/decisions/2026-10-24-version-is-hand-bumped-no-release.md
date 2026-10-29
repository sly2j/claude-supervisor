---
domain: code
summary: VERSION is hand-bumped; there are no tags, CI, hooks or release process; CHANGELOG.md lists major versions only
affects: [VERSION, CHANGELOG.md, CLAUDE.md, tests/test_version.py]
verified: 2026-10-29
source: .supervisor/archive/working/plans/plan-versioning.md; owner 2026-10-21
supersedes: .supervisor/archive/memory/decisions/2026-10-22-no-version-tags-hooks-or-release-process.md
---
Repo work only; deployed projects are untouched.
Why: the owner wants nothing beyond the one-line file and its test.
Rejected: a tracked pre-commit hook (inactive without `core.hooksPath` in every clone).

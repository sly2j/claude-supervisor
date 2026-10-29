---
domain: process
summary: VERSION tracks the primary deliverable; ancillary-only change sets (memory, dev docs, tests, plans) never bump it
affects: [CLAUDE.md, pack/skills/repo-workflow/SKILL.md, tests/test_version.py]
verified: 2026-10-29
source: user 2026-10-27
supersedes:
---
Only changes to the product raise the version; for writing-led projects the prime documents are the product, not dev-facing docs. Refines the hand-bumped scheme in .supervisor/memory/decisions/2026-10-24-version-is-hand-bumped-no-release.md.
Why: bumps for memory or documentation edits add noise that says nothing about the deliverable.
Rejected: versioning `tests/` (lint changes alter what pack edits can pass, not the deployed product); bumping on every commit.

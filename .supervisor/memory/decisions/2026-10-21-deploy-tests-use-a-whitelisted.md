---
domain: process
summary: Deploy tests use a whitelisted environment, a stub claude and per-test fixtures
affects: [tests/test_deploy.py, tests/]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-full-review.md#approach
supersedes:
---
The `deploy` test harness runs subprocesses with an environment built from a whitelist (`PATH`, `HOME`, `TMPDIR`, `LANG`, `LC_ALL`) plus explicit extras, never a copy of the developer's environment, because `CLAUDE_CODE_*`, `GIT_*` and `XDG_*` variables leak in and change behavior (notably the doctor tests). Tests run against a temp HOME. A `stub_claude(bin_dir, version)` helper writes an executable `claude` that answers `--version` and records other arguments, so `doctor` is testable on PATH without a real Claude Code.

Fixtures are rebuilt per test, including the bare remote repo, which dominates the suite runtime. Rejected: a session-scoped bare repo (couples tests to each other), and rewriting the in-process tests' HOME setup (no observed fragility).

Reach: repo work.

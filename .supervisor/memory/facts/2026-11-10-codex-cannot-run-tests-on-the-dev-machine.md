---
domain: code
summary: Codex's read-only Seatbelt sandbox runs Homebrew python3 (no pytest) but refuses the conda interpreter, so Codex cannot run the tests itself
affects: [pack/skills/supervisor-config/scripts/codex-critic]
verified: 2026-11-10
source: .supervisor/archive/working/plans/plan-codex-critic.md, user smoke test 2026-10-24
supersedes: .supervisor/archive/memory/facts/2026-11-10-codex-cannot-run-tests-on-the-dev-machine.md
---
On the dev machine Codex cannot independently run tests, so its review prompt asks for a VALIDATION note saying what was not run. The owner judged the Codex critic good as is, so no interpreter is named for its sandbox.

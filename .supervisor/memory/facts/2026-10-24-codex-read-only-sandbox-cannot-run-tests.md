---
domain: code
summary: Codex's read-only Seatbelt sandbox runs Homebrew python3 (no pytest) but refuses the conda interpreter, so Codex cannot run the tests itself
affects: [pack/skills/supervisor-config/scripts/codex-critic]
verified: 2026-10-24
source: .supervisor/archive/working/plans/plan-codex-critic.md, user smoke test 2026-10-24
supersedes: 
---
On the dev machine Codex cannot independently run tests, so its review prompt asks for a VALIDATION note saying what was not run. An interpreter-path setting for Codex test runs is a roadmap follow-up.

---
summary: Re-measure harness efficiency against the recorded baseline
status: blocked
owner: 
since: 
plan: 
depends: []
decisions:
  - .supervisor/memory/decisions/2026-10-24-every-lead-does-a-single-unit-itself-and.md .supervisor/memory/decisions/2026-10-24-tools-audit-is-opt-in-tooling.md
---
Goal: Tune the scope-critic skip condition and the executor single-unit rule on measured numbers.
Scope: Run python3 -I tools/audit/audit.py and compare with .supervisor/memory/facts/2026-10-24-efficiency-baseline-for-drift.md. Output is never committed.
Done when: The thresholds are tuned on the numbers, or kept with the numbers recorded.
Notes: Blocked: not before late November 2026, once a few weeks of v6.0 sessions exist.

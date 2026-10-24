---
domain: process
summary: supervisor.md word cap in the pack lint is raised minimally, to a multiple of 10; existing rules are not trimmed to fit an owner-requested rule
affects: [tests/test_pack_lint.py, pack/agents/supervisor.md]
verified: 2026-10-24
source: user 2026-10-24 ("you can raise the supervisor cap to the next round number because of this. Round numbres are multiples of 10.")
supersedes:
---
The `supervisor.md` word cap is raised from 1000 to the smallest multiple of 10 that fits the file after the writer-model rule (`decisions/2026-10-24-writer-lead-runs-on-fable.md`) is added; the exact number is in the lint, set by the executor's commit.
Rule for the future: cap raises are minimal and land on a multiple of 10. Existing rules are not trimmed to make room for an owner-requested rule.
Rejected: trimming existing supervisor rules to fit; a blanket raise (e.g. to 1100).

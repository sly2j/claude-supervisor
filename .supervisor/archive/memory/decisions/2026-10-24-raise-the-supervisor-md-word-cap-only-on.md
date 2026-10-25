---
domain: process
summary: Raise the supervisor.md word cap only on the owner's say-so, to the smallest multiple of 10 that fits; never trim rules to fit
affects: [tests/test_pack_lint.py, pack/agents/supervisor.md]
verified: 2026-10-24
source: user 2026-10-24 ("you can raise the supervisor cap to the next round number because of this. Round numbres are multiples of 10.")
supersedes: .supervisor/archive/memory/decisions/2026-10-24-raise-the-supervisor-word-cap-minimally.md
superseded by: .supervisor/memory/decisions/2026-10-24-raise-a-word-cap-only-on-the-owner-s-sa.md
---
A cap raise lands on the smallest multiple of 10 that fits the file, and only when the owner says so. Existing supervisor rules are not trimmed to make room for a rule the owner asked for.
Rejected: trimming existing rules to fit; a blanket raise (for example by 100).

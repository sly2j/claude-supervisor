---
domain: process
summary: Raising a pack word cap is owner-only; trim wording first via a redundancy audit; trimming or removing rules to fit needs the owner
affects: [tests/test_pack_lint.py, pack/agents/supervisor.md, pack/skills/lead-loop/SKILL.md]
verified: 2026-10-25
source: .supervisor/archive/working/research/research-supervisor-word-budget.md, user 2026-10-25
supersedes: .supervisor/archive/memory/decisions/2026-10-24-raise-a-pack-word-cap-only-on-the-owner.md
---
A cap raise, for `supervisor.md` or a skill, lands on the smallest multiple of 10 that fits the file, and only when the owner says so.
Over a cap, first try trimming wording: audit for redundancy against the files the reader actually loads, and cut only restatements. This needs no owner approval. A body over its cap through wording slack is fixed this way, not by a raise.
Trimming or removing rules to fit a cap is not allowed without the owner, nor is making room for a new rule by cutting existing ones.
Rejected: trimming rules to fit; a blanket raise (for example by 100).

---
domain: process
summary: The residue ledger is local-only, an exception to the committed store; one file per agent and a standalone skill, not a shared file or lead-loop text
affects: [pack/skills/residue/SKILL.md, pack/skills/project-memory/SKILL.md]
verified: 2026-10-27
source: .supervisor/archive/working/plans/plan-test-residue-cleanup.md#decisions (D1), user 2026-10-27
supersedes:
---
The ledger under `.supervisor/working/residue/` is excluded through git's `info/exclude`, unlike the rest of the committed store (`2026-10-24-the-store-is-committed-in-the-branch-and.md`).
Why: residue is machine-local or reachable only from the host that made it, so another clone cannot act on a committed entry, and excluding it keeps squashes, rebases and store commits free of ledger churn.
Rejected: a shared ledger file (concurrent writers race); the session scratchpad as ledger (not shared across agents or sessions); relaying ledger content through the supervisor; per-agent rules or `lead-loop` text instead of a preloaded skill (no word-cap headroom, workers never load `lead-loop`).
superseded by: .supervisor/memory/decisions/2026-10-29-the-residue-ledger-is-local-only-an-excep.md

---
domain: process
summary: Moved sources are resolved, not rewritten; a missing source: is found by name under working/ or archive/, else git log --all
affects: [pack/skills/project-memory/SKILL.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-memory-stage4.md#approach
supersedes:
---
A `source:` path that no longer exists names a moved file: find the same name under
`.supervisor/working/` or `.supervisor/archive/`, else run `git log --all -- <path>`. Entries are
never edited and `history.md` is append-only, so the `source:` lines that cite the old
`docs/archive/` plan paths stay as written.

Why: file names keep their `research-`/`plan-` prefixes across the move, so lookup by name works.
Rejected: rewriting `source:` lines (breaks supersede-never-edit); superseding the entries that
cite a moved file (churn with no new claim).

Reach: product; stated in `pack/skills/project-memory/SKILL.md` (Entries).

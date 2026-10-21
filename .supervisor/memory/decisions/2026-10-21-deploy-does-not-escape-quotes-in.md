---
domain: process
summary: Deploy does not escape quotes in launcher values or lock the registry; reviewers do not flag either
affects: [deploy]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-full-review.md#findings
supersedes:
---
A full review of `deploy` considered and rejected several hardenings; a later reviewer would raise them again. In force:
- Launcher values (config dir, prefix, base URL, token path) are written inside plain single quotes without escaping. Real values carry no quote characters, and several tests pin the quoted form.
- The install registry (`installs.json`) is read-modify-written without a lock across targets: one sequential process per user writes it, and `update --all` is sequential.
- An empty `--target ""` or `--prefix ""` silently falls back to the default (an empty `--tag` is rejected); no failure was observed.
- Frontmatter parsing does not strip a UTF-8 BOM, because `deploy` reads only the repo's own `pack/` files, which carry none.
Reopen one only on an observed failure.

Reach: repo work; written into REVIEW.md ("Do not report").

---
domain: process
summary: Review-only rules live in REVIEW.md, kept to one screen; CLAUDE.md keeps edit, test, deploy and commit rules
affects: [REVIEW.md, CLAUDE.md]
verified: 2026-10-24
source: .supervisor/archive/working/plans/plan-full-review.md#approach
supersedes: .supervisor/archive/memory/decisions/2026-10-21-review-only-rules-live-in-review-md-one.md
---
This repo splits rules by audience: `CLAUDE.md` holds what an editing agent must do (edit, test, deploy, commit); `REVIEW.md` holds what a reviewer must check (always-check rules per area, severity calibration, the evidence a finding needs). A rule only about reviewing goes in `REVIEW.md`; nothing is duplicated between them.
Why: Anthropic's Code Review and the pack's `critic` both read `REVIEW.md`. It stays within about 40 lines, since a longer file buries the severity rules reviewers most need.
Rejected: growing `REVIEW.md` with edge cases of the review mechanism; moving `CLAUDE.md` rules into it.

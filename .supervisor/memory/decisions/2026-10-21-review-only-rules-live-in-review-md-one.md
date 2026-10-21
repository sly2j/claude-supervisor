---
domain: process
summary: Review-only rules live in REVIEW.md, kept to one screen; CLAUDE.md keeps edit, test, deploy and commit rules
affects: [REVIEW.md, CLAUDE.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-full-review.md#approach
supersedes:
---
This repo splits its rules by audience. `CLAUDE.md` holds what an editing agent must do (edit, test, deploy and commit rules). `REVIEW.md` holds what a reviewer must check: always-check rules per area, severity calibration (what is BLOCKING, what is SHOULD, what not to report), and the evidence a finding needs. A rule that is only about reviewing goes in `REVIEW.md`; nothing is duplicated between them.

Why: Anthropic's Code Review and the pack's `critic` both read `REVIEW.md`, and `CLAUDE.md` held no review-only rule when the split was made. `REVIEW.md` stays short enough to read in one screen (about 40 lines at most): a longer file buries the severity rules reviewers most need. Rejected: growing `REVIEW.md` with edge cases of the review mechanism, and moving `CLAUDE.md` rules into it.

Reach: repo work.

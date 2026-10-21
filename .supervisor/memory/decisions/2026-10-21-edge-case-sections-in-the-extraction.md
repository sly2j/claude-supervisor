---
domain: process
summary: Edge-case sections in the extraction skills stay despite restating rules (user decision)
affects: [pack/skills/document-extraction/SKILL.md, pack/skills/email-extraction/SKILL.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-full-review.md#open-questions
supersedes:
---
During the full review, clauses that read as anticipated-failure rules or restate earlier rules were candidates for deletion. The user approved deleting the ones in the planner, scope-critic, lead-loop and conflict-resolution files, but reverted the deletion of the `Edge cases` sections of `document-extraction` and `email-extraction`: they stay as they are. A reviewer must not flag them as pure restatements.

The general test the review used: a clause stays when an observed failure stands behind it; delete it only when the user recalls none. The same bar applies to new rules (the review rule is that a new rule cites an observed failure).

Reach: repo work.

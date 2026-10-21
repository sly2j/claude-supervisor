---
domain: process
summary: The critic discovers REVIEW.md itself; precedence is the contract, then REVIEW.md, then critic defaults
affects: [pack/agents/critic.md, REVIEW.md, docs/architecture.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-full-review.md#approach
supersedes:
---
`critic` finds and applies a project's `REVIEW.md` on its own: the one at the repo root plus any in a directory holding a changed file (code reviews) or holding the artifact (research, plan, prose and agent-definition reviews). Precedence: the contract in the brief, then `REVIEW.md`, then the critic's own defaults; `REVIEW.md` never overrides the user's decisions.

Why: discovery inside the critic also serves the supervisor's ad hoc reviews, which have no lead brief, and the same file is what Anthropic's Code Review reads. Rejected: having the lead pass `REVIEW.md` in the critic's brief (misses ad hoc reviews and adds a step to every lead); a checklist file inside the pack (`REVIEW.md` is a project file and is not word-capped). Consequence: `critic.md` carries one `Project rules` bullet; leads' briefs are unchanged.

Reach: product; stated in pack/agents/critic.md:35.

---
domain: process
summary: The install-time allow rule covers only codex-critic review, not enable, so an in-session enable costs one prompt by design
affects: [deploy, pack/skills/supervisor-config/scripts/codex-critic]
verified: 2026-10-29
source: .supervisor/archive/working/plans/plan-codex-critic.md, user 2026-10-24
supersedes: 
---
Each install allows `codex-critic review *` only. `enable`, `disable` and `status` still prompt.
Why: a rule covering the whole script would let an agent turn Codex on and skip the user's consent; one prompt per enable is the price.
Rejected: allowing the whole script; allowing enable.

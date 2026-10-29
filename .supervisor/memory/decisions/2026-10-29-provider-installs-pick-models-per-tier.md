---
domain: code
summary: Provider installs pick models per tier by picker or flag, except a preset that knows its ids defaults them; subscription installs never prompt
affects: [deploy, docs/deploy.md]
verified: 2026-10-29
source: .supervisor/archive/working/plans/plan-argo-preset.md; user 2026-10-29
supersedes: .supervisor/archive/memory/decisions/2026-10-27-provider-installs-pick-models-per-tier.md
---
Subscription and `--global` installs never detect the plan or model and never prompt. Provider installs map the four tiers through a filterable picker, `--model-<tier>` flags, and an error listing the flags with no TTY. The Argo preset instead defaults the tiers (Fable and Opus to the Opus id), also at an argo-proxy `--base-url`, because the proxy accepts the same ids.
Why: a generic provider has no known tier models, so the user chooses; Argo's ids are known, and the proxy fronts the same backend.
Rejected: tier defaults only at Argo's own URL; `--opus` and `--no-fable` flags (creep).

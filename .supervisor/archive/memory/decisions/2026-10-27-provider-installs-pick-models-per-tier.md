---
domain: code
summary: Provider installs pick models per tier interactively or by flag; subscription installs never prompt about the model
affects: [deploy, docs/deploy.md]
verified: 2026-10-29
source: .supervisor/archive/working/plans/api-access-install.md; user 2026-10-27
supersedes: .supervisor/archive/memory/decisions/2026-10-24-deploy-never-detects-the-plan-or-model.md
superseded by: .supervisor/memory/decisions/2026-10-29-provider-installs-pick-models-per-tier.md
---
Subscription and `--global` installs never detect the plan or model: no prompt, no auto value, no saved Fable choice. Provider installs (`--provider` or `--base-url`) map the four tiers to the provider's models through a filterable per-tier picker, `--model-<tier>` flags for scripts, and an error listing the flags when there is no TTY.
Why: a provider has no default tier models, so the user must choose; the plan-detection design read an undocumented field seen on one account and still had to ask.
Rejected as creep: `--opus` and `--no-fable` flags.

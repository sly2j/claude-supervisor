---
domain: code
summary: On a provider profile --fable-is-opus maps Fable to the Opus-tier model picked for that profile, never a Claude model id
affects: [deploy, docs/deploy.md]
verified: 2026-10-27
source: .supervisor/archive/working/plans/api-access-install.md; user 2026-10-27
supersedes:
---
The flag exports the profile's Opus-tier pick as `ANTHROPIC_DEFAULT_FABLE_MODEL`; subscription profiles keep the pinned Opus id.
Why: a Claude model id does not exist on a third-party provider.

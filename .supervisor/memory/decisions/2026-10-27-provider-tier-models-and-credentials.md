---
domain: code
summary: Provider tier models and credentials live in launcher exports, never in the profile's settings.json env
affects: [deploy, docs/deploy.md]
verified: 2026-10-27
source: .supervisor/archive/working/plans/api-access-install.md
supersedes:
---
Tier models, base URL and tokens are exported by the launcher; install adds only `apiKeyHelper` to `settings.json`, and filters `ANTHROPIC_*` from the seeded `env` on provider installs.
Why: a settings `env` value outranks the launcher's export, so a per-session `--fable-is-opus` could never override it, and secrets stay out of settings files.
Rejected: tier values in settings `env`; `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY` (feeds `/model`, not the tier aliases); a bundled bridge for OpenAI-only endpoints (not stdlib, needs a resident process).

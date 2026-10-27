---
domain: code
summary: Expiring provider tokens use a managed apiKeyHelper and no static ANTHROPIC_AUTH_TOKEN; a static token flag replaces the helper
affects: [deploy, docs/deploy.md]
verified: 2026-10-27
source: .supervisor/archive/working/plans/api-access-install.md
supersedes:
---
A profile has either a static token (`<dir>/token`) or a managed `apiKeyHelper`, never both. A helper install removes the token file and the launcher unsets `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY`; a static-token flag on re-install wins over a preset's helper default and removes the managed helper.
Why: a static export outranks the helper and never refreshes, so ALCF's 48-hour tokens would silently expire.

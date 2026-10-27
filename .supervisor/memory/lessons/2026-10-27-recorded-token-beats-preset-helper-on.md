---
domain: code
summary: On re-install of a provider profile, a recorded static token must win over the preset's helper default, or the profile gets both.
affects: [deploy]
verified: 2026-10-27
source: user 2026-10-27
supersedes:
---
When re-installing a provider profile, check for a recorded static token before applying the preset's `apiKeyHelper` default; the token wins and no helper is added.
Why: applying the preset default first left a profile holding both a token and an `apiKeyHelper`; a critic found it as a blocking defect (api-access-install plan, .supervisor/archive/working/plans/api-access-install.md, commit d81b1a5).

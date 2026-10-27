---
domain: process
summary: Every major version change (X.0 bump) adds a CHANGELOG.md entry in the same change set
affects: [CHANGELOG.md, VERSION, CLAUDE.md]
verified: 2026-10-27
source: user 2026-10-27
supersedes:
superseded by: CLAUDE.md (rule and tests/ now carry it; no entry remains)
---
The change set that raises X adds the CHANGELOG.md entry for that major version; minor bumps get none.
Why: a major landed without one and the changelog is the only readable record of major versions.
Rejected: backfilling afterwards, which is how the miss happened.

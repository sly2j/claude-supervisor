---
domain: process
summary: Every migrate run is exempt from the entry cap
affects: [pack/agents/curator.md, pack/skills/project-memory/references/curator-procedures.md]
verified: 2026-10-21
source: user 2026-10-21
supersedes:
---
User, verbatim: "OQ4: yes migrations are a special case."

User, verbatim, later the same day: "any migration as this likely will come up for any project we're migrating from one of the older versions".

The five-entry cap (`curator.md`: at most five new entries per run unless the brief says otherwise) does not apply to any `migrate` run, for any project migrating from an older pack layout, including the Stage 4 (P3) `curator migrate docs/` run. The brief lifts the cap, so the owner reviews all new entries (about 30 in P3) in one `git diff` instead of six runs. Ordinary runs keep the cap.

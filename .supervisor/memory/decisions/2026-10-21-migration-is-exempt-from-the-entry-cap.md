---
domain: process
summary: Migration is exempt from the entry cap, one-time run only
affects: [pack/agents/curator.md, pack/skills/project-memory/references/curator-procedures.md]
verified: 2026-10-21
source: user 2026-10-21
supersedes:
---
User, verbatim: "OQ4: yes migrations are a special case."

The five-entry cap (`curator.md`: at most five new entries per run unless the brief says otherwise) does not apply to the one-time `curator migrate docs/` run of Stage 4 (P3). Its brief lifts the cap, so the owner reviews all new entries (about 30) in one `git diff` instead of six runs. The exemption covers that one-time run only; whether later migrations are exempt is not decided here. Ordinary runs keep the cap.

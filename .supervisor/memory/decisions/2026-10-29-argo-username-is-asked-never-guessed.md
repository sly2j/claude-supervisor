---
domain: code
summary: The Argo username is asked on a terminal and an error without one; it never defaults silently to $USER
affects: [deploy, docs/deploy.md]
verified: 2026-10-29
source: .supervisor/archive/working/plans/plan-argo-preset.md; user 2026-10-29
supersedes:
---
The Argo preset's token is the user's ANL domain username, passed with `--username` (sugar for the helper `echo NAME`). A missing one is prompted for with `$USER` as the default, or is an error naming the flag when there is no terminal or `--yes`.
Why: the ANL username can differ from `$USER`, and a wrong one passes every install check and surfaces only as a 401 inside Claude Code.
Rejected: defaulting silently to `$USER`; a static `--token NAME` recipe (the helper form is the only one known to work, since Claude Code sends its output as both `X-Api-Key` and `Bearer`).

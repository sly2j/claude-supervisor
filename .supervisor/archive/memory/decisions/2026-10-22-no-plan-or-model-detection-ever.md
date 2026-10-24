---
domain: code
summary: Deploy never detects the plan or model; Opus is the default and Fable a per-session opt-in
affects: [deploy, docs/deploy.md]
verified: 2026-10-24
source: .supervisor/archive/working/plans/plan-opus-default.md; user 2026-10-21
supersedes: .supervisor/archive/memory/decisions/2026-10-22-deploy-install-model-rationale.md
superseded by: .supervisor/memory/decisions/2026-10-24-deploy-never-detects-the-plan-or-model.md
---
No plan or model detection, no prompt, no `auto` value and no saved Fable choice.
Why: the first design read the plan from `claude auth status --json` and an undocumented `~/.claude.json` field seen on one Team account, and still had to ask when unclear. Rejected as creep: `--opus` and `--no-fable` flags.

---
domain: code
summary: --global installs get a printed note, not an Opus remap; the user sets ANTHROPIC_DEFAULT_FABLE_MODEL themselves
affects: [deploy, docs/deploy.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#decisions
supersedes:
---
A `--global` install (straight into `~/.claude`) has no launcher, so `deploy` cannot export `ANTHROPIC_DEFAULT_FABLE_MODEL` for it and the Fable agents run on Fable there. The owner decided a printed note plus documentation is enough: `install --global` prints "set ANTHROPIC_DEFAULT_FABLE_MODEL to run fable agents on Opus", and `docs/deploy.md` gives the shell-profile form and the `~/.claude/settings.json` `env` form. `deploy` does not manage the variable for global installs.

Reach: product; stated in docs/deploy.md:130.
superseded by: .supervisor/memory/decisions/2026-10-22-launcher-design-rationale.md

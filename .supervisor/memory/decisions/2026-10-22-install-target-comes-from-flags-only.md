---
domain: code
summary: Install target comes from flags only; CLAUDE_CONFIG_DIR is ignored and ~/.claude is never a profile
affects: [deploy, docs/deploy.md]
verified: 2026-10-24
source: .supervisor/archive/working/plans/plan-sandboxed-install.md; user 2026-10-21
supersedes: .supervisor/archive/memory/decisions/2026-10-22-deploy-install-model-rationale.md
---
A profile is the default and `--global` the opt-in; the target comes from `--tag`/`--target`, never from `$CLAUDE_CONFIG_DIR`, and a profile resolving to `~/.claude` is refused.
Why: the variable must not silently pick the target; profile uninstall would delete `~/.claude`; the Keychain login follows the literal dir string (see the CLAUDE_CONFIG_DIR fact). Rejected: `~/.claude` as default. Not built: an `XDG_CONFIG_HOME` default.

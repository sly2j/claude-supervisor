---
domain: code
summary: Launcher design rationale: baked config dir, claude from PATH, first-argument commands, Fable remapped to Opus with --fable opt-out
affects: [deploy, docs/deploy.md, README.md]
verified: 2026-10-22
source: .supervisor/archive/working/research/research-sandboxed-install.md; .supervisor/archive/working/plans/plan-install-lifecycle.md; user 2026-10-22
supersedes: [.supervisor/archive/memory/decisions/2026-10-21-the-launcher-is-a-marked-0755-script.md, .supervisor/archive/memory/decisions/2026-10-21-launcher-subcommands-use-first-arg-2.md, .supervisor/archive/memory/decisions/2026-10-21-launcher-remaps-fable-to-opus-installed-2.md, .supervisor/archive/memory/decisions/2026-10-21-global-installs-get-a-note-not-an-opus.md]
superseded by: .supervisor/memory/decisions/2026-10-22-fable-remapped-by-launcher-env-var.md
---
Behaviour is in `deploy` (`launcher_text`, `LAUNCHER_HELP`, `OPUS_MODEL`) and `docs/deploy.md`
(checked against `deploy`, 2026-10-22); this keeps the why, tradeoffs and rejected options.

- The launcher is a regular 0755 file, never a symlink, carrying a marker on line 2: uninstall
  removes only marked files and install refuses an unmarked path. Tags cannot make `claude-<tag>`
  equal `claude`, so it cannot recurse. The config dir is baked as an absolute path because the
  Keychain login follows the literal string.
- `claude` is looked up on `PATH` at run time so the launcher follows Claude Code updates and passes
  arguments through. Tradeoff accepted: every tag runs the same Claude Code version; pinning a
  `versions/<v>` path is fragile (the native installer keeps two versions) and stays out of scope.
- Commands (`update`, `uninstall`, `list`, `status`) dispatch on the first argument and run the
  prefix's tool copy. Tool-selecting flags are refused rather than silently ignored; the tool copy
  still accepts the old appended form because older launchers use it. `update` runs `claude update`
  first (a new pack can need a newer Claude Code) and still updates the pack if that fails. The
  deploy call runs before the config dir is exported so `claude update` sees the user's normal
  environment. `uninstall` requires typing the tag (it deletes sessions, history, login); `--yes`
  skips prompts, no terminal refuses; `uninstall --all` is refused from a launcher. Help and
  version stay first-argument only because claude has subcommands with their own help
  (`claude-<tag> mcp --help`); `--fable`, the only own session flag, counts anywhere before `--`
  (owner 2026-10-22: flags must not depend on position). Dispatch is not generalised.
- Fable is remapped, not rewritten: deployed agent files keep `model: fable` and the launcher exports
  `ANTHROPIC_DEFAULT_FABLE_MODEL` as a full model ID (the variable requires one), updated by hand
  per Opus release, then `install` regenerates launchers. Why: Fable is billed separately on some
  plans, so Opus is the default and Fable a per-session choice. The prose `model: fable` dispatch
  overrides follow the remap with no pack edit; the owner's by-hand check that such a dispatch really
  reports Opus was still open, so treat that as assumed. Rejected: `CLAUDE_CODE_SUBAGENT_MODEL`
  (overrides every subagent, Haiku and Sonnet included) and an install-time rewrite plus an install
  `--fable` flag and manifest key (the earlier design).
- `--global` installs have no launcher, so they get a printed note and docs (shell-profile and
  `settings.json` `env` forms) instead of an Opus remap; `deploy` does not manage the variable there.

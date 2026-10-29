---
domain: code
summary: CLAUDE_CONFIG_DIR gives each dir its own login; the Keychain entry is keyed to the literal dir string
affects: [deploy, docs/deploy.md]
verified: 2026-10-29
source: .supervisor/archive/working/research/research-sandboxed-install.md#1-is-claude_config_dir-the-supported-mechanism
supersedes: .supervisor/archive/memory/facts/2026-10-21-claude-config-dir-gives-each-dir-a-login.md
---
Observed on macOS with a native Claude Code 2.1.302 install, from the official docs plus local observation.
- `CLAUDE_CONFIG_DIR` is the documented way to run Claude Code against another config dir. Settings, history, plugins, `.claude.json` and credentials live under it, so each dir needs its own `/login`.
- The macOS Keychain entry is `Claude Code-credentials-<first 8 hex of sha256(dir)>` when the variable is set, plain `Claude Code-credentials` when unset. The hash input is the literal string (NFC only, no `~` expansion); community reports say `$HOME/.claude` selects a different entry than unset.
For `deploy`: a launcher bakes the absolute resolved path, never expands `$HOME` at run time (a different string silently switches logins), and never points at `~/.claude`. Not tested: interactive `/login` in a profile, Linux credential isolation, IDE integration.

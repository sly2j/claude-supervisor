---
domain: code
summary: CLAUDE_CONFIG_DIR gives each dir its own login; the Keychain entry is keyed to the literal dir string
affects: [deploy, docs/deploy.md]
verified: 2026-10-24
source: .supervisor/archive/working/research/research-sandboxed-install.md#1-is-claude_config_dir-the-supported-mechanism
supersedes:
---
Found 2026-10-16 on Claude Code 2.1.302 (macOS, native install), from the official docs plus local observation; not re-checked since.

- `CLAUDE_CONFIG_DIR` is the documented way to run Claude Code against another config dir. Settings, session history, plugins, `.claude.json` (OAuth account, onboarding state, user-scope MCP servers) and credentials live under it, so each dir needs its own `/login` (or `ANTHROPIC_API_KEY`). Project and local settings ignore the variable.
- On macOS the Keychain entry is `Claude Code-credentials-<first 8 hex of sha256(dir)>` when the variable is set, and plain `Claude Code-credentials` when it is not. The hash input is the literal string (NFC only, no `~` expansion). Community reports say that setting the variable to `$HOME/.claude` selects a different entry than leaving it unset (so the login looks lost) and that a Keychain ACL bug can force a re-login after reboot.

Consequences for `deploy`: a launcher must bake the absolute path the deploy resolved, never expand `$HOME` or `XDG_CONFIG_HOME` at run time (a different string would silently switch logins), and must never point at `~/.claude`. Every tag needs its own login. Profile uninstall leaves that dir's Keychain entry behind, which is harmless, and re-installing at the same path reuses it. Not tested: interactive `/login` in a profile, Linux credential isolation, IDE integration with a custom dir.

Reach: product; enforced in deploy (target resolution).

superseded by: .supervisor/memory/facts/2026-10-24-claude-config-dir-gives-each-dir-its-own.md

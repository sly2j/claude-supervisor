---
domain: code
summary: The launcher is a marked 0755 sh script that execs claude from PATH with a baked absolute config dir
affects: [deploy, docs/deploy.md]
verified: 2026-10-21
source: .supervisor/archive/working/research/research-sandboxed-install.md#4-launcher
supersedes:
---
Each sandbox install writes `<prefix>/bin/claude-<tag>`: a regular file (never a symlink), mode 0755, written atomically, with the marker `# managed by claude-supervisor (tag: <tag>)` on line 2. Uninstall removes only files carrying the marker, and install refuses a launcher path that exists without it (a directory, or someone else's file) and one that already launches a different config dir. Tags match `[A-Za-z0-9_-]+`, so `claude-<tag>` can never equal `claude` and cannot recurse into itself.

The script exports `CLAUDE_CONFIG_DIR` set to the absolute path baked in at install time (the Keychain login follows the literal string; see the entry on `CLAUDE_CONFIG_DIR` and logins), then ends with `exec claude "$@"`. `claude` is looked up on `PATH` at run time so the launcher follows Claude Code updates and passes arguments through unchanged (spaces, `--`, empty args). Tradeoff accepted: every tag runs the same Claude Code version. Running different versions side by side would need a baked `versions/<v>` path, which is fragile because the native installer keeps only the two newest versions; version pinning stays out of scope. Install warns when `<prefix>/bin` is not on `PATH`.

Reach: product; stated in deploy:733.
superseded by: .supervisor/memory/decisions/2026-10-22-launcher-design-rationale.md

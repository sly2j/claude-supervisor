---
domain: code
summary: Sandbox installs are the default, --global is opt-in, and the target comes from flags only
affects: [deploy, docs/deploy.md, README.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-sandboxed-install.md#approach
supersedes:
---
`deploy install` installs into a sandbox by default: a tag (default `supervisor`) and a dir (default `~/.config/claude-<tag>`, or `--target DIR`), plus a `claude-<tag>` launcher. `--global` keeps the older behaviour (the pack goes into `~/.claude`, no seeding, no launcher, manifest-driven uninstall). Why: the owner wanted the pack available as its own session type without turning plain `claude` into the supervisor, and a separate config dir gives each tag its own login, settings and history.

Target resolution uses flags only. `$CLAUDE_CONFIG_DIR` is ignored (it must not silently pick the target), and conflicting flags are errors: `--global` combined with `--tag`, `--target`, `--base-url`, `--token` or `--token-file` fails with exit 2, and so does an invalid tag. A sandbox whose dir resolves to `~/.claude` is refused ("use --global"): otherwise sandbox uninstall would delete `~/.claude`, and a launcher pointing `CLAUDE_CONFIG_DIR` at the default dir selects a different macOS Keychain entry than plain `claude`, so the login looks lost.

Rejected: keeping `~/.claude` as the default with sandboxes as an option (plain `claude` would keep starting as the supervisor), and honouring `$CLAUDE_CONFIG_DIR`. Consequence: anyone who used `$CLAUDE_CONFIG_DIR` to pick a target must now pass `--target`, which creates a sandbox. Out of scope when this was decided and still not built: launchers for `--global` installs, model or subscription detection, and an `XDG_CONFIG_HOME` default.

Reach: product; stated in deploy:199.

---
domain: code
summary: A new sandbox is seeded once from an allowlist of ~/.claude; logins, plugins and runtime state are never copied
affects: [deploy, docs/deploy.md, README.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-sandboxed-install.md#approach
supersedes:
---
The first install of a sandbox (no manifest yet) copies the user's own items from `~/.claude`: `settings.json`, `CLAUDE.md`, `commands/`, `output-styles/`, `keybindings.json`, and the user's own files under `agents/` and `skills/`. Pack files come from the install itself, so files listed in the global manifest are skipped, as are `skills/.trash`, `skills/synced` (account-synced dirs) and `*.bak-*`. Directories are copied as copies, not symlinks into the global dir.

`settings.json` is copied without its `agent` key. Otherwise a fresh sandbox would record the copied `"agent": "supervisor"` as not managed by the pack, and `--no-default-agent` could not remove it. The install then claims the key through its normal settings step.

Never copied: `.claude.json` and credentials (they carry the login identity, and each config dir has its own), `backups/` (holds `oauthAccount` copies), `projects/`, `sessions/`, `history.jsonl`, caches, logs and every other runtime-state entry, and `plugins/`. Plugins stay behind because the plugin registries hold absolute paths into the old root, so a verbatim copy would read another root's files; users reinstall plugins inside the sandbox. Copied `hooks` in `settings.json` keep working only while their commands avoid `~/.claude` paths.

Seeding happens only when the sandbox has no manifest (and per item only when the sandbox does not already hold it), never on re-install, so edits made inside the sandbox are not overwritten. A failed copy removes the partial item and aborts, because a partial copy would make every re-run skip that item as already seeded.

Reach: product; stated in deploy:41.
superseded by: .supervisor/memory/decisions/2026-10-22-deploy-install-model-rationale.md

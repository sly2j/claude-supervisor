---
domain: code
summary: Sandbox uninstall needs a manifest and deletes the whole dir; global uninstall removes only unmodified pack files
affects: [deploy, docs/deploy.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-sandboxed-install.md#approach
supersedes:
---
Without a manifest, `uninstall` is a no-op (it says so, prunes a stale registry entry, and mentions that the directory still exists), so the deploy never deletes a dir it did not create. With a manifest, a sandbox uninstall deletes the entire dir, including sessions, history, login and `token`, and its launcher, and removes the registry entry. It confirms first with the prompt "Delete <dir> (sessions, history, login) and its launcher?"; the launcher is deleted only when it carries the marker, otherwise it is left in place with a warning. No settings restore is needed because the whole dir goes.

`--global` uninstall stays manifest-driven: it removes unmodified managed files (all with `--force`), prunes empty dirs under `skills/` and `agents/`, restores the previous `agent` setting, and deletes the manifest and lock. It never removes `~/.claude` itself, `settings.json` or `*.bak-*` files. `uninstall --all` asks once, listing every target ("deletes sessions, history, login" for sandboxes), then runs this path per entry.

Reach: product; stated in deploy:1082.
superseded by: .supervisor/memory/decisions/2026-10-22-deploy-install-model-rationale.md

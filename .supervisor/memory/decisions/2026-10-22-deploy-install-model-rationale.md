---
domain: code
summary: Deploy install model rationale: sandbox default, flags-only target, stand-alone installs, small registry, recorded-remote update, seed allowlist
affects: [deploy, docs/deploy.md, README.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-sandboxed-install.md, plan-install-lifecycle.md, plan-versioning.md, plan-opus-default.md (same dir); user 2026-10-21
supersedes: [.supervisor/archive/memory/decisions/2026-10-21-sandbox-installs-are-the-default.md, .supervisor/archive/memory/decisions/2026-10-21-sandbox-uninstall-needs-a-manifest.md, .supervisor/archive/memory/decisions/2026-10-21-installs-are-standalone-of-the-deploy.md, .supervisor/archive/memory/decisions/2026-10-21-update-clones-the-recorded-remote-and.md, .supervisor/archive/memory/decisions/2026-10-21-a-per-prefix-installsjson-registry-maps.md, .supervisor/archive/memory/decisions/2026-10-21-prefix-scopes-the-launcher-and-registry.md, .supervisor/archive/memory/decisions/2026-10-21-a-new-sandbox-is-seeded-once-from-an.md, .supervisor/archive/memory/decisions/2026-10-21-pack-version-is-read-from-version-beside.md, .supervisor/archive/memory/decisions/2026-10-21-no-plan-or-model-detection-opus-is-the.md]
---
Behaviour is in `deploy` and `docs/deploy.md` (checked against `deploy`, 2026-10-22); this keeps the
why, the rejected options and the consequences.

Sandbox default
- Sandbox is the default and `--global` opt-in: the owner wanted the pack as its own session type
  without turning plain `claude` into the supervisor, and a separate config dir gives each tag its
  own login, settings and history.
- Target comes from flags only. `$CLAUDE_CONFIG_DIR` is ignored (it must not silently pick the
  target); anyone who used it must pass `--target`. A sandbox dir resolving to `~/.claude` is
  refused ("use --global"): sandbox uninstall would delete `~/.claude`, and a launcher pointing
  `CLAUDE_CONFIG_DIR` at the default dir selects a different macOS Keychain entry, so the login
  looks lost. Rejected: `~/.claude` as default. Not built: `XDG_CONFIG_HOME` default.
- Sandbox uninstall needs a manifest, so `deploy` never deletes a dir it did not create; without
  one it is a no-op that says so. With one it deletes the whole dir after a confirmation prompt.
  Global uninstall stays manifest-driven and never touches `~/.claude` itself, `settings.json` or
  `*.bak-*`.
- Seeding copies an allowlist once, on a sandbox's first install, never on re-install, so edits
  made inside survive. Never copied: logins and credentials (each config dir has its own login;
  `backups/` holds `oauthAccount` copies), runtime state, and `plugins/` (their registries hold
  absolute paths into the old root; users reinstall plugins in the sandbox). `settings.json` is
  copied without its `agent` key, or the sandbox would record it as not pack-managed and
  `--no-default-agent` could not remove it. A failed copy removes the partial item and aborts, since
  a partial copy would be skipped on re-run as already seeded.

Stand-alone installs (user 2026-10-21: "like any other program it has to be stand-alone")
- An installed instance must not depend on the source checkout, which may move, change or be
  deleted. Version and update info come from the install's own record (manifest, `installs.json`,
  a `VERSION` copy beside the tool copy). Any run-time need for the checkout is a defect unless the
  user names one (`update --from`); reading the recorded checkout is allowed only as an extra whose
  absence changes no result (`status` says "source not available", never MISMATCH).
- `--prefix` scopes launcher, registry and tool copy (it replaced `--bin-dir`, with no shim), so
  tests and dev worktrees need not touch the real install, and a recorded launcher path alone could
  not be recomputed. Prefixes are independent; a manifest recording another prefix makes install
  and single uninstall refuse before any write.
- The registry maps each target to `tag`, `remote`, `branch` only; everything else is in the
  manifest, and a second copy would drift. Left out: extra fields, a repair or import command,
  `$XDG_STATE_HOME` (not asked for; `--prefix` moves the state dir), `status --all` (`list`
  replaces it).
- `update` clones the recorded remote and runs the clone's own `deploy update --from`, so the newest
  code replays each install's recorded options: the old copy would replay flags newer code removed
  (the removed `--fable` install flag was the case). Consequences: it needs git and network; it
  sees only what is pushed to the followed branch (push before relying on it); installs from before
  the registry need one `./deploy install`; after an update the manifest's `source_dir` is a deleted
  temp clone, so `status` needs `--source` to compare.

Version and Fable
- The pack version is read from the `VERSION` beside the installed `pack/` (`source.parent`), not
  from where `deploy` runs, so it is right when `--source` points at another clone and tests need no
  environment hook. A missing file is not an error (recorded as null); `status` exits 0 on MISMATCH
  (owner decision).
- No plan or model detection, ever, and no prompt, `auto` value or saved Fable choice: the first
  design read the plan from `claude auth status --json` and an undocumented `~/.claude.json` field
  seen on one Team account, and still had to ask when unclear. Opus is the default; Fable is a
  per-session opt-in via the launcher. Rejected as creep: `--opus` or `--no-fable` flags.

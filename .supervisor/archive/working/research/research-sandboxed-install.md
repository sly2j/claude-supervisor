# Research: Sandboxed Installs With A Launcher (ROADMAP Item 2)

Scope: facts for planning item 2. Covers `CLAUDE_CONFIG_DIR` support, what to copy from `~/.claude`,
today's target handling in `scripts/deploy`, and the launcher shape. Gathered 2026-10-16 on macOS
with Claude Code 2.1.302 (native install). Labels: **[V]** verified (official docs or local
observation), **[I]** inference, **[C]** community report (GitHub issue).

## 1. Is `CLAUDE_CONFIG_DIR` The Supported Mechanism?

Yes. It is documented, and the docs show the launcher pattern itself as an alias.

- [V] https://code.claude.com/docs/en/env-vars (the `CLAUDE_CONFIG_DIR` row): "Override the
  configuration directory (default: `~/.claude`). All settings, session history, and plugins are
  stored under this path ... `alias claude-work='CLAUDE_CONFIG_DIR=~/.claude-work claude'`".
  Project and local settings ignore it, and a settings file must give an absolute path.
- [V] https://code.claude.com/docs/en/authentication#log-in-with-multiple-accounts: "Each
  directory has its own settings, session history, and claude.ai login or API key". A new dir
  starts with login and setup, so each tag needs its own `/login` (or `ANTHROPIC_API_KEY`).
  Console sign-ins without an API key are stored outside the config dir.
- [V] https://code.claude.com/docs/en/authentication#credential-management: with
  `CLAUDE_CONFIG_DIR` set, `.credentials.json` lives under that dir, and Claude Code "keys the
  macOS Keychain entry to that directory too".
- [V] Binary strings (2.1.302): the Keychain service is `Claude Code-credentials-<sha256(dir)[:8]>`
  when the variable is set, else `Claude Code-credentials`. The hash input is the literal string
  (NFC only, no `~` expansion). `.claude.json` resolves to `$CLAUDE_CONFIG_DIR/.claude.json`, so the
  OAuth account, onboarding state, and user-scope MCP servers are per dir. `history.jsonl`,
  `projects/`, `jobs/`, `daemon/`, `shell-snapshots/`, `session-env/`, and `ide/` also live there;
  the IDE lockfile search additionally checks `~/.claude/ide`.
- [I] `agents/`, `skills/`, `commands/`, and `CLAUDE.md` follow the same root ("all settings ...
  under this path"). This was not traced file by file.
- Caveats:
  - [C] https://github.com/anthropics/claude-code/issues/92252 (open, macOS): setting
    `CLAUDE_CONFIG_DIR=$HOME/.claude` selects a different Keychain entry than leaving the variable
    unset, so the login looks lost. A launcher must never point at the default dir.
  - [C] https://github.com/anthropics/claude-code/issues/20553 (open): per-dir hashed entries have
    shipped since about 2.1.56. A remaining Keychain ACL bug may force a re-login after reboot.
  - [C] https://github.com/anthropics/claude-code/issues/79223 (open):
    `CLAUDE_SECURESTORAGE_CONFIG_DIR` overrides the hashed dir and is undocumented.

## 2. Inventory Of `~/.claude` And `~/.claude.json`

[V] `~/.claude` has 32 top-level entries, none of them symlinks. Absent: `.credentials.json` (the
login is in the Keychain), `CLAUDE.md`, `commands/`, `output-styles/`, `keybindings.json`.

| Entry | Size | Class | Note |
|---|---|---|---|
| `settings.json` | 2 KB | COPY | Keys `agent`, `hooks`, `theme`. Hook commands point outside `~/.claude` only. |
| `agents/` | 14 files | COPY (pack) | All 14 are listed in the manifest, so the pack install provides them. |
| `skills/` | 8.7 MB | COPY (pack paths only) | 11 skills are manifest-listed. `.trash/` and `synced/` (account-synced UUID dirs) are not pack files. |
| `plugins/` | 27 MB | UNCLEAR | The registries hold absolute paths (below). Most of the rest is re-fetchable cache. |
| `projects/`, `sessions/`, `session-env/`, `history.jsonl`, `file-history/`, `shell-snapshots/`, `paste-cache/`, `jobs/`, `tasks/`, `state/`, `daemon/`, `daemon.log`, `debug/`, `telemetry/`, `cache/`, `chrome/`, `bridge-spawn/`, `downloads/` | - | NEVER | Transcripts, live session keys, history, runtime state, caches, logs, and machine-bound files. |
| `backups/` | 420 KB | NEVER | Holds `.claude.json.backup.*`, which contain `oauthAccount`. |
| `policy-limits.json`, `remote-settings.json` (+ stamps), `.last-cleanup`, `.last-update-result.json` | tiny | NEVER | Account-synced or runtime state, regenerated. |
| `.claude-supervisor-manifest.json`, `.claude-supervisor.lock`, `settings.json.bak-*` | tiny | NEVER | Deploy bookkeeping. Each target writes its own. |

- [V] Plugin registries: `installed_plugins.json` `installPath` and all three
  `known_marketplaces.json` `installLocation` values are absolute, pointing into `~/.claude` and
  into a second config root outside it. A verbatim copy would read another root's files.
- [V] `~/.claude.json` (84 KB, mode 600) is the global-mode state file. Its keys include
  `oauthAccount`, `userID`, `machineID`, `projects`, and `installMethod: native`. It has no
  `mcpServers` key. With the variable set, Claude Code reads `$CLAUDE_CONFIG_DIR/.claude.json`
  instead.
- [V] `~/.local/bin` already holds `claude-mag` (a launcher that sets `CLAUDE_CONFIG_DIR`), a
  `claude-swap` symlink, and a `claude-config/` directory.

Recommended lists [I]:
- **Copy**:
  - `settings.json`, minus its `agent` key when the global manifest marks that key managed.
    Otherwise a fresh sandbox (no manifest) records the copied `"supervisor"` as unmanaged, and
    `--no-default-agent` cannot remove it (`scripts/deploy:394-407`).
  - `CLAUDE.md`, `commands/`, `output-styles/`, and `keybindings.json`, when present.
  - Non-manifest files under `agents/` and `skills/`, without `skills/.trash` and `skills/synced`.
    Pack files come from the install itself, not from the copy.
- **Never**: `.claude.json` (in or outside the dir, because it carries the login identity),
  credentials, `backups/`, and every NEVER row in the table.
- **Unclear, owner decides**: `plugins/`. Either (a) skip it and reinstall plugins inside the
  sandbox, which is simpler, or (b) copy the two registries and rewrite their paths.
- Copied `hooks` keep working only while their commands avoid `~/.claude` paths.

## 3. `scripts/deploy` Today

- [V] `resolve_target` (`scripts/deploy:118-120`; the ROADMAP pointer :116 is stale): `--target`,
  else `$CLAUDE_CONFIG_DIR`, else `~/.claude`, then `expanduser().resolve()`. Callers: install
  (:439), status (:606), uninstall (:644), doctor (:726). `--target` is defined once in `common()`
  (:818-819) for all four. The default is also hardcoded at :2, :814, :819,
  `docs/deploy.md:20,24`, and `README.md` (19, 26, 151-160).
- [V] Manifest `<target>/.claude-supervisor-manifest.json` (:27), keys at :548-558: `version`,
  `source_dir`, `source_commit`, `source_dirty`, `pack_version`, `installed_at`, `files`,
  `settings` (`managed_agent_key`, `previous_agent`), `fable`. Written :565, read :332-344, legacy
  migration :315-329.
- [V] `status` (:605-638) reads only the target's manifest, files, and `settings.json`.
- [V] `uninstall` (:643-711) is a no-op without a manifest (:646-648). It removes unmodified
  managed files (all with `--force`), prunes empty dirs except `agents/` and `skills/` (:426-435),
  restores the `agent` key (:670-691), and deletes manifest and lock (:693-703). It never removes
  the target dir, `settings.json`, or `*.bak-*`.
- [V] `doctor` only prints the target and reads its manifest and settings (:733, :754, :773).
- [V] `target_lock` (:347-362) runs `mkdir(parents=True)`, so a new `~/.config/claude-<tag>` needs
  no extra code. A dry run creates nothing.
- [V] Install writes `"agent": "supervisor"` into `<target>/settings.json` (`plan_settings`,
  :386-421), so the main thread starts as `supervisor` (`docs/deploy.md:20,35`).
  `--force-default-agent` replaces another value and saves it in the manifest;
  `--no-default-agent` skips the step. Writes are crash-ordered, after a `.bak-<ts>` (:559-569).
- [V] Tests: `run()` (`tests/test_deploy.py:45-54`) always passes `--target <tmp>`, strips
  `CLAUDE_CONFIG_DIR`, and sets `HOME=<tmp>`. No test covers the default target or the env var.
- [I] Implications for the planner:
  - Define precedence: `$CLAUDE_CONFIG_DIR` can no longer silently pick the target (:119), and
    `--tag`/`--global` vs `--target` needs a rule (for example, mutually exclusive).
  - Tagged uninstall needs new code to remove the dir. It should refuse or confirm when the dir
    holds files the deploy did not create. The global path can stay as is.
  - The existing global install needs a migration rule. `~/.claude` holds a manifest and a
    managed `agent` key today. Once the default moves, `status` and `uninstall` without `--global`
    will not see it, and plain `claude` keeps starting as `supervisor`.
  - A tagged install that keeps setting the `agent` key gives "pack in a sandbox" behavior, and
    plain `claude` is unaffected.

## 4. Launcher

- [V] `claude` resolves to `~/.local/bin/claude` (`command -v -a` gives one hit). It is a symlink
  to `~/.local/share/claude/versions/2.1.302`, the native layout
  (https://code.claude.com/docs/en/setup#auto-updates), and the docs name only that symlink and
  `~/.local/share/claude/` as installer-managed. The installer does not add `~/.local/bin` to PATH
  (https://code.claude.com/docs/en/troubleshoot-install); here it is on PATH.
- [V] `claude --help` lists no `--fable` flag. `--model fable` exists.
- [I] No recursion: `claude-<tag>` can never equal `claude`. Validate tags as
  `^[A-Za-z0-9][A-Za-z0-9._-]*$`, and refuse an existing launcher path that lacks the marker or is
  a directory (`config`, `mag`, and `swap` already collide here).
- [I] Use `exec claude "$@"` (PATH lookup at run time) so the launcher follows updates. Tradeoff:
  every tag runs the same Claude Code version. The goal "try Claude Code versions side by side"
  would need a baked `versions/<v>` path, which is fragile because the installer keeps only the
  two newest versions (setup docs). The owner decides.
- [I] Bake the config path as the absolute string the deploy resolved. The Keychain hash depends on
  the literal string, so expanding `$HOME` or `XDG_CONFIG_HOME` at run time could silently switch
  logins.
- [I] Write the launcher as a regular file, mode 0755, atomically. Put a marker on line 2 so
  uninstall removes only launchers it created. Warn when the prefix is not on PATH.

Minimal shape. It was tested with a stub `claude`, is `sh -n` clean, and keeps spaces, `--`, and
empty args intact.

```sh
#!/bin/sh
# managed by claude-supervisor (tag: supervisor)
CLAUDE_CONFIG_DIR='/Users/<user>/.config/claude-supervisor'; export CLAUDE_CONFIG_DIR
exec claude "$@"
```

Room for item 6 [I]: ROADMAP item 6 fixes the flag as `--fable`, and today's `claude` has no such
flag. The launcher would branch on a leading flag
(`if [ "${1-}" = --fable ]; then shift; else export <VAR>=...; fi`) before `exec`, passing the
remaining args through unchanged.

## Gaps

- Not tested: interactive `/login` in a sandbox dir, Linux credential isolation (issue #47661
  reports a leak), IDE integration with a custom dir, and per-dir updater state.
- The `plugin-*-cache.json` files were not scanned.
- How `agents/` and `skills/` are looked up under `CLAUDE_CONFIG_DIR` was not traced in the binary.

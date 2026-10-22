# Deploying claude-supervisor

This runbook is for a human or for Claude asked to "deploy claude-supervisor". It works on macOS and Linux and needs `python3` (3.9 or newer), `git` (to clone, and for `update`) and Claude Code 2.1.293 or newer.

## Steps

First time:

```bash
git clone https://github.com/sly2j/claude-supervisor.git ~/Work/claude-supervisor
REPO=~/Work/claude-supervisor
```

From an existing checkout (see Update):

```bash
REPO=~/Work/claude-supervisor
cd "$REPO" && git pull
```

Then, in either case:

```bash
"$REPO/deploy" doctor        # preflight: python, claude version, env overrides (warns "not installed yet" on a fresh machine)
"$REPO/deploy" install --dry-run
"$REPO/deploy" install       # sandbox ~/.config/claude-supervisor + launcher (fable agents run on Opus; see Fable Or Opus)
"$REPO/deploy" status
"$REPO/deploy" doctor        # should now report no FAIL
```

Start it with `claude-supervisor` and log in once; each sandbox has its own login, settings, and history, and plain `claude` is untouched. The session runs as `supervisor` because install sets `"agent": "supervisor"` in the sandbox's `settings.json`. Type `/agents` to see the installed agents.

If `install` prints `WARNING <bin> is not on your PATH; add export PATH="<bin>:$PATH" to your shell profile, then open a new terminal`, `claude-supervisor` will not be found until that line is in the shell profile (`<bin>` is `~/.local/bin` by default).

`doctor`, `status`, `update` and `uninstall` take the same `--tag` or `--global` (and `--prefix`) as the install.

## What Install Does

- Copies `pack/agents/*.md` to `<target>/agents/` and `pack/skills/*` to `<target>/skills/`. The target is a sandbox, `~/.config/claude-<tag>` (`--tag`, default `supervisor`; `--target DIR` sets another dir), or `~/.claude` with `--global`, which installs as before with no copy and no launcher. `$CLAUDE_CONFIG_DIR` is ignored.
- Records SHA-256 hashes in `<target>/.claude-supervisor-manifest.json`. An install made before the rename (with `.claude-agents-manifest.json`) is still recognized by `status` and is migrated to the new name by the next `install`. Re-running `install` is the update path and is idempotent:

| Situation | Action |
|---|---|
| File not installed yet | copied |
| Installed and unmodified, source changed | updated |
| You edited the installed file | kept, with a warning (`--overwrite-local` backs it up as `<file>.bak-<timestamp>` and replaces it) |
| A file with that name exists that the pack does not manage | refused, exit code 1 (`--overwrite-local` backs it up and replaces it) |
| File removed from the pack | deleted if unmodified, otherwise kept and handed over to you |

- Sets `"agent": "supervisor"` in `settings.json`. It backs up the file first, writes atomically, and keeps every other key. If you already have a different `agent`, the script leaves it alone unless you pass `--force-default-agent`. `--no-default-agent` skips this step (and restores your previous value if the pack had set it). Start the supervisor with `claude-supervisor --agent supervisor`. `claude-supervisor --agent <other>` overrides the setting for a single session.
- Validates every source agent and skill before writing anything, and holds a lock so two deploys cannot run at once.
- Records the checkout's current git branch next to the remote in the registry; `update` follows it. A detached HEAD records `main` and prints a one-line warning; a source that is not a git checkout records `main` silently. `status` prints `Remote: <url or none>` and `Branch: <branch>` from the registry, or `Remote: not registered`.
- Records the checkout's version as `pack_version` in the manifest and prints `Version: <version>`, with `(was <old>)` on an update. `VERSION` (the file next to `pack/`) holds the `main` version only; the install derives its version from git. On `main` it is plain `X.y`, also when the tree is dirty. On any other branch (or a detached HEAD) it is `<VERSION at the merge-base with main>+<branch>.<commits ahead of main>.g<short sha>`, plus `.dirty` when the pack dir has uncommitted changes, for example `2.3+memory-v2.7.g8b1d7de`. In the branch name, characters other than letters, digits, `.` and `-` become `-`. The base is `origin/main`, else local `main`; with neither, the version is plain `X.y`. Nothing needs editing after a rebase. `status`, `list` and `--version` use the same derived version. `status` prints `Version: installed=<version>, source=<version>` and appends `(MISMATCH: run ./deploy install from your checkout)` when they differ. When the recorded source dir is gone or no longer a valid pack (for example after `update`) and `--source` is not given, `status` prints `Source: <dir> (not available; pass --source <checkout>/pack to compare)` and `Version: installed=<version> (source not available)` with no MISMATCH, and reports file states (ok, modified, missing) from the manifest alone. Manifests from before versioning show `installed=not recorded` until the next install.
- On a sandbox's first install, copies from `~/.claude`: `settings.json` (without `agent`), `CLAUDE.md`, `commands/`, `output-styles/`, `keybindings.json`, and your own files in `agents/` and `skills/` (not `skills/.trash` or `skills/synced`). Plugins, logins, history, and sessions stay behind.
- Writes the launcher `<prefix>/bin/claude-<tag>` (`--prefix P`, default `~/.local`), which runs `claude` with `CLAUDE_CONFIG_DIR` set to the sandbox. The sandbox dir does not depend on the prefix. The manifest records the prefix, and `install` and `uninstall` refuse a different `--prefix` for an existing install (exit code 2, with the prefix to pass). Install also refuses a tag whose launcher path exists and was not written by the deploy.

### Token Provider

```bash
"$REPO/deploy" install --tag work --base-url https://llm.example.com --token-file ~/work.token
```

Use this only for a proxy or gateway; omit it to use a normal login. Install copies the token to `<dir>/token` (mode 0600), and the launcher exports `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`. `--token VALUE` also works but leaves the value in your shell history, so prefer `--token-file`. A later plain `install` keeps both; `--base-url ''` drops the URL, and deleting `<dir>/token` drops the token at the next install.

## The Launcher

```bash
claude-supervisor update              # claude update, then this sandbox's pack
claude-supervisor update --all        # every install in this launcher's prefix
claude-supervisor uninstall           # delete this sandbox
claude-supervisor status              # this sandbox's version and file states
claude-supervisor list                # every install in this launcher's prefix
claude-supervisor --version           # pack and claude versions (or -v)
claude-supervisor -h                  # the launcher's own help (or --help, help)
```

For commands, the launcher checks only its first argument. `update`, `uninstall`, `status` and `list` run the deploy tool copy under the launcher's own prefix (`<prefix>/state/claude-supervisor/deploy`), always for this launcher's install: `--tag`, `--target`, `--prefix` and `--global` are refused with exit code 2 (use the deploy tool for other installs), and their help and errors name `claude-<tag>`. `-v`/`--version` and `-h`/`--help`/`help` are answered by the launcher itself. `--fable` counts in any position before a `--`, also with a command, where it has no effect. Everything else, including unknown flags, goes to `claude` unchanged, so `claude-supervisor -p update`, `claude-supervisor --resume` and `claude-supervisor doctor` (Claude Code's own) still reach `claude`. Replace `supervisor` with your `--tag`.

- `update` asks y/N, then runs `claude update` first, because a new pack can need a newer Claude Code, and then updates the pack from the remote and branch recorded at install, like `deploy update --tag <tag>`. If `claude update` fails, it says so and still updates the pack; the exit code is 1 if either step failed. `--yes` skips the question, and `--dry-run` shows what would change, including "would run claude update".
- `uninstall` deletes this sandbox (its dir with sessions, history, login and token, its launcher, and its registry entry). It asks you to type the tag to confirm; `--yes` skips that. `uninstall --all` is refused from a launcher; use the deploy tool's `uninstall --all`.
- Without a terminal, both need `--yes` (exit code 2 otherwise).
- If the tool copy is missing, the launcher prints `claude-<tag>: <path> missing; run ./deploy install from your checkout` and exits 1.
- `status` reports this install as `deploy status` does; when the recorded source dir is gone, it suggests `./deploy status --source <checkout>/pack` to compare.
- `-h` / `--help` / `help` prints the launcher's commands, its tag and config dir, and a note that `install` and `doctor` run from the checkout.
- `-v` / `--version` prints `claude-supervisor <installed pack version> (claude-<tag>, <config dir>)` and a `claude: <version>` line (`claude: not found` if it is missing).
- `--fable`, in any position before a `--`, runs that session on Fable; see Fable Or Opus.
- If `claude` is not on `PATH`, a session start prints `claude-<tag>: claude not found on PATH; install Claude Code, then retry` and exits 127.
- `--global` installs have no launcher; use the deploy tool.

## Update

Every install records itself in a registry, `<prefix>/state/claude-supervisor/installs.json`, and writes a copy of the deploy tool to `<prefix>/state/claude-supervisor/deploy` (by default under `~/.local/state/claude-supervisor/`), with the version of the install that last wrote it beside it in `<prefix>/state/claude-supervisor/VERSION` (removed when the source has no `VERSION`). An install is stand-alone: nothing it runs depends on the source checkout existing or being unchanged, and version and update information come from what the install recorded. The registry file and tool copy stay after uninstall (the install's entry is removed). Each prefix has its own registry and tool copy, and installs under different prefixes are independent: `update` and `uninstall` (and `--all`) act on the registry of the `--prefix` you give. The commands below use the default prefix; add `--prefix P` for another.

```bash
~/.local/state/claude-supervisor/deploy update                # the default sandbox; or "$REPO/deploy" update
~/.local/state/claude-supervisor/deploy update --tag work     # another sandbox (--target DIR, or --global)
~/.local/state/claude-supervisor/deploy update --all --yes    # every registered install
~/.local/state/claude-supervisor/deploy list                  # what is registered
```

`list [--prefix DIR]` shows each install in that prefix's registry: tag, target, installed version, branch, commit (short, with `-dirty` if the source was dirty), and whether the launcher exists (`yes`, `missing`, or `-` for `--global` or when there is no readable manifest). `./deploy --version` prints the checkout's derived pack version and the `claude:` line; the tool copy's `--version` (`~/.local/state/claude-supervisor/deploy --version`) prints the version recorded by the install that last wrote the tool copy, without the checkout.

`update` clones the branch recorded at install from the git remote recorded at install into a temp dir (shallow for `main`; full history for other branches, so the merge-base with `main` is available for the version) and reinstalls with each install's recorded options (prefix, `--no-default-agent`, base URL and token). It works without the checkout, but it needs git and network or ssh access, and it only sees what is pushed to that branch. `--all` groups installs by remote and branch and asks once before changing anything. `--yes` skips that question and `--dry-run` shows the changes. `update --from DIR --all` updates only the installs whose remote and branch match DIR's checkout.

If an install is newer than what `update` would install (main version first, then commits ahead), `update` prints a WARNING naming both versions and asks `Continue with the update? [y/N]`. The default is No: the install is left unchanged and the exit code is 1. Without a terminal it fails (exit code 2) unless `--yes` is passed, and `--dry-run` only warns.

Installs made before this version are not registered, and their launchers have no `update` or `uninstall` subcommands. Run `"$REPO/deploy" install` once from the checkout; it registers the install and rewrites the launcher. An install with no recorded remote (the source was not a git checkout) errors; update it with `--from DIR`, where DIR is a checkout. Registry entries from before branches were recorded count as `main`.

If the recorded branch is gone from the remote, `update` leaves that install unchanged and prints `STALE <target>: nothing to update; branch <b> is gone from <remote>; this install is stale. Remove it with: claude-<tag> uninstall (or ./deploy uninstall --tag <tag> --target <target>)` (a `--global` install says `./deploy uninstall --global`). Under `--all` the other installs still update, and the exit code is 3. A network or auth failure reaching the remote is an error (exit code 1), not stale.

After an update, `status` shows `Version: installed=<version> (source not available)` and file states from the manifest, because the manifest names the deleted clone. Pass `--source "$REPO/pack"` to compare versions.

### Dev Worktree Install

To try a feature branch next to your normal install, give it its own worktree and tag:

```bash
git -C "$REPO" worktree add ../claude-supervisor-dev -b my-feature
"$REPO/../claude-supervisor-dev/deploy" install --tag supervisor-dev
claude-supervisor-dev            # runs the branch's pack
git -C "$REPO/../claude-supervisor-dev" push -u origin my-feature
claude-supervisor-dev update     # pulls the pushed my-feature branch
```

`update` follows the pushed branch, so push it first. The install's version is derived from the branch (such as `2.3+my-feature.2.g8b1d7de`), so unpushed commits make it newer than the pushed branch and `update` asks before downgrading it. To deploy unpushed edits, run `./deploy install --tag supervisor-dev` from the worktree. Once the branch is deleted from the remote, `update` reports the install as stale (exit code 3); remove it with `claude-supervisor-dev uninstall`.

## Fable Or Opus

Three agents (`supervisor`, `planner`, `scope-critic`) are written for Fable, and `planner` and `writer` also name `model: fable` in their dispatch instructions. Deployed files always say `model: fable`, byte for byte as in `pack/`. Fable is billed to usage credits on some plans, so each launcher exports `ANTHROPIC_DEFAULT_FABLE_MODEL=claude-opus-5-5`, which makes those agents and dispatch overrides run on Opus. `claude-<tag> ... --fable` strips the flag, unsets the variable and runs that session on Fable. The flag counts in any position before a `--`; the other arguments reach `claude` in their order.

The value is a full model ID, the `OPUS_MODEL` constant in `deploy`. When a new Opus ships, update the constant and re-run `install` to regenerate the launchers.

`--global` installs have no launcher, so `install --global` prints a note and the agents run on Fable until you set the variable yourself, in a shell profile or in `~/.claude/settings.json`:

```bash
export ANTHROPIC_DEFAULT_FABLE_MODEL=claude-opus-5-5
```

```json
{ "env": { "ANTHROPIC_DEFAULT_FABLE_MODEL": "claude-opus-5-5" } }
```

A sandbox created later copies `~/.claude/settings.json`, and there the settings value overrides `--fable`, so use the shell-profile form if you also use sandboxes.

Global installs made before 1.14 had those files rewritten to `opus`; the next plain `install` restores `model: fable` without `--overwrite-local`.

## Doctor Checks

| Check | Level | Meaning and remedy |
|---|---|---|
| python >= 3.9 | FAIL | Deploy needs 3.9 or newer |
| `claude` on `PATH` | FAIL | Install Claude Code and open a new terminal |
| `claude --version` readable | FAIL | Reinstall Claude Code |
| `claude --version` >= 2.1.293 | FAIL | Older versions lack Haiku 5.5, per-agent `effort`, or nested subagents; run `claude update` |
| Manifest readable | FAIL | Restore it from a backup, or delete it and re-run `./deploy install` (existing files then need `--overwrite-local`) |
| Pack installed (manifest exists) | WARN | Pack not installed in the target yet; run `./deploy install` from your checkout (the one expected WARN before install) |
| Managed files missing | FAIL | Run `./deploy install` |
| Managed files modified | WARN | Keep them, or run `./deploy install --overwrite-local` |
| `settings.json` parses | FAIL | Fix the JSON |
| `settings.json` `agent` is `supervisor` | WARN | Run `./deploy install` (`--force-default-agent` replaces another agent); skipped when no manifest exists |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` < 2 | WARN | Leads cannot dispatch workers, so Mode 1 breaks; unset it, or remove it from `settings.json` `env` |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` set | WARN | Every agent runs on one model, so model tiering is lost; unset it, or remove it from `settings.json` `env` |
| `CLAUDE_CODE_EFFORT_LEVEL` set | WARN | Per-agent effort levels are ignored; unset it, or remove it from `settings.json` `env` |
| `git` | WARN | Needed for `./deploy update` and to clone; optional otherwise (`git-ops` uses it) |
| `zip` | WARN | Optional; used by `project-backup` |

The three environment variables are checked both in the shell environment and in the `env` block of the target's `settings.json`. Doctor exits 1 if any row is FAIL; WARN rows do not change the exit code.

Anthropic's document skills are recommended for docx, pdf, pptx, and xlsx work, but doctor does not check for them. Inside a claude-supervisor session, run `/plugin marketplace add anthropics/skills`, then install `document-skills`.

## Uninstall

```bash
"$REPO/deploy" uninstall --dry-run
"$REPO/deploy" uninstall --yes
```

For a sandbox, uninstall deletes its dir, including sessions, history, login, and token, and its launcher. With `--global` it removes only the pack's files. Either way it removes the install's registry entry.

`uninstall --all` removes every install registered under the given `--prefix` after one confirmation that lists them. Entries whose target has no manifest are pruned from the registry.

Uninstall removes the unmodified managed files and keeps the ones you edited; `--force` removes those as well. It restores your previous `agent` setting.

## Migrate

```bash
"$REPO/deploy" migrate
```

`migrate` moves a pack installed straight into `~/.claude` (versions before 1.10) to the default sandbox, after one confirmation:

1. It finds the old install by its manifest in `~/.claude`: `.claude-supervisor-manifest.json`, or `.claude-agents-manifest.json` (lock `.claude-agents.lock`) for installs from before 1.6.
2. It copies the pack files you edited to a timestamped backup directory at the top level of `~/.claude`, removes all of the pack's files and its manifest, and restores the `agent` setting as `uninstall` does. `settings.json` is backed up first; nothing else in `~/.claude` is touched besides these backups.
3. It installs and registers the default sandbox and its launcher, as `install` does.
4. It checks that `~/.local/bin` is on `PATH`.

With no old install, it just installs. It removes edited pack files too, after the backup: a pack file left in `~/.claude` without its manifest is seeded into the next new sandbox and refused as unmanaged. Plain `claude` then starts plain Claude Code.

## Notes For Claude Running This

- Run the commands through Bash exactly as shown. Without a terminal, `uninstall`, `install --overwrite-local`, `update --all`, `uninstall --all`, `migrate`, `claude-<tag> update` and `claude-<tag> uninstall` need `--yes`.
- If install reports kept local modifications or unmanaged collisions, show the user the list and ask before re-running with `--overwrite-local`.
- If doctor reports a FAIL, report it and its fix. Do not edit the user's shell profile (including the PATH line `install` prints) or environment variables without asking.
- Exit codes: 0 means success, 1 means a file or settings step failed (see the output), a `doctor` row was FAIL, or a prompt was aborted (declined or Ctrl-D), 2 means a usage error, a failed source validation, a held lock, or an OS error such as an unreadable path, and 3 means `update` found an install whose recorded branch is gone from its remote.
- If `status` shows `MISMATCH`, the installed pack is not the checkout's version: run `install`. `(source not available)` is not a mismatch; pass `--source "$REPO/pack"` to compare.

# Deploying claude-supervisor

This runbook is for a human or for Claude asked to "deploy claude-supervisor". It works on macOS and Linux and needs only `python3` (3.9 or newer) and Claude Code 2.1.293 or newer.

## Steps

```bash
# first time:
git clone https://github.com/sly2j/claude-supervisor.git ~/Work/claude-supervisor
REPO=~/Work/claude-supervisor
cd "$REPO" && git pull               # when updating from the checkout (see Update)

"$REPO/deploy" doctor        # preflight: python, claude version, env overrides (warns "not installed yet" on a fresh machine)
"$REPO/deploy" install --dry-run
"$REPO/deploy" install       # sandbox ~/.config/claude-supervisor + launcher; add --fable to deploy the Fable agents on Fable (see Fable Or Opus)
"$REPO/deploy" status
"$REPO/deploy" doctor        # should now report no FAIL
```

Start it with `claude-supervisor` and log in once; each sandbox has its own login, settings, and history, and plain `claude` is untouched. The session runs as `supervisor` because install sets `"agent": "supervisor"` in the sandbox's `settings.json`. Type `/agents` to see the installed agents.

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
- Records the checkout's `VERSION` (the file next to `pack/`) as `pack_version` in the manifest and prints `Version: 1.x`, with `(was 1.y)` on an update. `status` prints `Version: installed=1.x, source=1.y` and appends `(MISMATCH: run deploy install)` when they differ. Manifests from before versioning show `installed=not recorded` until the next install.
- On a sandbox's first install, copies from `~/.claude`: `settings.json` (without `agent`), `CLAUDE.md`, `commands/`, `output-styles/`, `keybindings.json`, and your own files in `agents/` and `skills/` (not `skills/.trash` or `skills/synced`). Plugins, logins, history, and sessions stay behind.
- Writes the launcher `<prefix>/bin/claude-<tag>` (`--prefix P`, default `~/.local`), which runs `claude` with `CLAUDE_CONFIG_DIR` set to the sandbox. The sandbox dir does not depend on the prefix. The manifest records the prefix, and `install` and `uninstall` refuse a different `--prefix` for an existing install (exit code 2, with the prefix to pass). Install also refuses a tag whose launcher path exists and was not written by the deploy.

### Token Provider

```bash
"$REPO/deploy" install --tag work --base-url https://llm.example.com --token-file ~/work.token
```

Install copies the token to `<dir>/token` (mode 0600), and the launcher exports `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`. `--token VALUE` also works but leaves the value in your shell history, so prefer `--token-file`. A later plain `install` keeps both; `--base-url ''` drops the URL, and deleting `<dir>/token` drops the token at the next install.

## Update

Every install records itself in a registry, `<prefix>/state/claude-supervisor/installs.json`, and writes a copy of the deploy tool to `<prefix>/state/claude-supervisor/deploy` (by default under `~/.local/state/claude-supervisor/`). Neither is ever deleted. Each prefix has its own registry and tool copy, and installs under different prefixes are independent: `update` and `uninstall` (and `--all`) act on the registry of the `--prefix` you give. The commands below use the default prefix; add `--prefix P` for another.

```bash
~/.local/state/claude-supervisor/deploy update                # the default sandbox; or "$REPO/deploy" update
~/.local/state/claude-supervisor/deploy update --tag work     # another sandbox (--target DIR, or --global)
~/.local/state/claude-supervisor/deploy update --all --yes    # every registered install
```

`update` shallow-clones `main` from the git remote recorded at install into a temp dir and reinstalls with each install's recorded options (prefix, `--no-default-agent`, `--fable`, base URL and token). It works without the checkout, but it needs git and network or ssh access, and it only sees what is pushed to `main`. `--all` asks once before changing anything. `--yes` skips that question and `--dry-run` shows the changes.

Installs made before this version are not registered. Run `"$REPO/deploy" install` once from the checkout. An install with no recorded remote (the source was not a git checkout) errors; update it with `--from DIR`, where DIR is a checkout.

After an update, `status` needs `--source "$REPO/pack"` to compare versions, because the manifest names the deleted clone.

## Fable Or Opus

Three agents (`supervisor`, `planner`, `scope-critic`) are written for Fable, and `planner` and `writer` also name `model: fable` in their dispatch instructions. `install` deploys those agents and dispatch overrides as `opus`; `install --fable` deploys the source verbatim, on Fable. Only files under `agents/` change; skills and the source in `pack/` always name Fable.

Each `install` deploys what its flag says, so pass `--fable` on every install that should stay on Fable. The manifest records the choice and `status` prints it as a `Fable:` line.

## Doctor Checks

| Check | FAIL / WARN meaning |
|---|---|
| `claude --version` >= 2.1.293 | Older versions lack Haiku 5.5, per-agent `effort`, or nested subagents |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` < 2 | Leads cannot dispatch workers, so Mode 1 breaks |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` set | Every agent runs on one model, so model tiering is lost |
| `CLAUDE_CODE_EFFORT_LEVEL` set | Per-agent effort levels are ignored |
| git, zip | Optional tools used by `git-ops` and `project-backup` |

Anthropic's document skills are recommended for docx, pdf, pptx, and xlsx work, but doctor does not check for them. In Claude Code, run `/plugin marketplace add anthropics/skills`, then install `document-skills`.

## Uninstall

```bash
"$REPO/deploy" uninstall --dry-run
"$REPO/deploy" uninstall --yes
```

For a sandbox, uninstall deletes its dir, including sessions, history, login, and token, and its launcher. With `--global` it removes only the pack's files. Either way it removes the install's registry entry.

`uninstall --all` removes every install registered under the given `--prefix` after one confirmation that lists them. Entries whose target has no manifest are pruned from the registry.

Uninstall removes the unmodified managed files and keeps the ones you edited; `--force` removes those as well. It restores your previous `agent` setting.

## Moving From A Global Install

Versions before 1.10 installed into `~/.claude`. After the first sandboxed install, remove that copy once:

```bash
"$REPO/deploy" uninstall --global --yes
```

Plain `claude` then starts plain Claude Code.

## Notes For Claude Running This

- Run the commands through Bash exactly as shown. Without a terminal, `uninstall`, `install --overwrite-local`, `update --all` and `uninstall --all` need `--yes`.
- If install reports kept local modifications or unmanaged collisions, show the user the list and ask before re-running with `--overwrite-local`.
- If doctor reports a FAIL, report it and its fix. Do not edit the user's shell profile or environment variables without asking.
- Exit codes: 0 means success, 1 means a file or settings step failed (see the output), and 2 means a usage error, a failed source validation, or a held lock.
- If `status` shows `MISMATCH`, the installed pack is not the checkout's version: run `install`.

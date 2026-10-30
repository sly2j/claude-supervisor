# Deploying Supervisor for Claude

This runbook is for a human or for Claude asked to "deploy Supervisor for Claude". It works on macOS and Linux and needs `python3` (3.9 or newer), `git` (to clone, and for `update`) and Claude Code 2.1.293 or newer.

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

Then, in either case, install into a profile: a private Claude Code config dir (`~/.config/claude-<tag>`) with its own launcher, login, settings and history; plain `claude` is untouched.

```bash
"$REPO/deploy" doctor        # preflight: python, claude version, env overrides (warns "not installed yet" on a fresh machine)
"$REPO/deploy" install --dry-run
"$REPO/deploy" install       # profile ~/.config/claude-supervisor + launcher (fable agents run on Fable unless the environment says otherwise; see Fable Or Opus)
"$REPO/deploy" status
"$REPO/deploy" doctor        # should now report no FAIL
```

Start it with `claude-supervisor` and log in once. The session runs as `supervisor` because install sets `"agent": "supervisor"` in the profile's `settings.json`. Type `/agents` to see the installed agents.

If `install` prints `WARNING <bin> is not on your PATH; add export PATH="<bin>:$PATH" to your shell profile, then open a new terminal`, `claude-supervisor` will not be found until that line is in the shell profile (`<bin>` is `~/.local/bin` by default).

`doctor`, `status`, `update` and `uninstall` take the same `--tag` or `--global` (and `--prefix`) as the install.

## What Install Does

- Copies the pack's agents and skills into the target: a profile, `~/.config/claude-<tag>` (`--tag`, default `supervisor`; `--target DIR` for another dir), or `~/.claude` with `--global`, which has no launcher. `$CLAUDE_CONFIG_DIR` is ignored.
- Re-running `install` is the update path and is safe to repeat. Install tracks the files it wrote, so your edits survive:

| Situation | Action |
|---|---|
| File not installed yet | copied |
| Installed and unmodified, source changed | updated |
| You edited the installed file | kept, with a warning (`--overwrite-local` backs it up as `<file>.bak-<timestamp>` and replaces it) |
| An unmanaged file with that name exists | refused, exit code 1 (`--overwrite-local` backs it up and replaces it) |
| File removed from the pack | deleted if unmodified, otherwise kept and handed over to you |

- Sets `"agent": "supervisor"` in `settings.json` and keeps every other key. A different `agent` you set is left alone unless you pass `--force-default-agent`; `--no-default-agent` skips this step. `claude-supervisor --agent <other>` overrides it for one session.
- In a profile, also sets the commit attribution in `settings.json`, so commits and PRs made by the agents carry only `Co-Authored-By: Supervisor for Claude`, with no session link and no "Generated with Claude Code" footer. A value you set yourself is left alone, and the install message says so.
- Checks the whole pack before writing anything.
- Records the checkout's remote and branch; `update` follows them. `status` prints both.
- Prints `Version: <version>`, with `(was <old>)` on an update (see Versions).
- On a profile's first install, copies from `~/.claude`: `settings.json` (without `agent`), `CLAUDE.md`, `commands/`, `output-styles/`, `keybindings.json`, and your own files in `agents/` and `skills/` (not `skills/.trash` or `skills/synced`). Plugins, logins, history, and sessions stay behind.
- Writes the launcher `<prefix>/bin/claude-<tag>` (`--prefix P`, default `~/.local`), which runs `claude` with the profile as its config dir. Later `install` and `uninstall` runs must use the same `--prefix`; the error names it. Install refuses a tag whose launcher path holds a file it did not write.

### Versions

A `main` install shows `X.y`. A branch install shows e.g. `2.3+my-feature.7.g8b1d7de` (base version, branch, commits ahead of `main`, commit, `.dirty` if uncommitted). `status`, `list` and `--version` show the same version.

### Token Provider

```bash
"$REPO/deploy" install --tag work --base-url https://llm.example.com --token-file ~/work.token
```

Routes the profile through a proxy or gateway that serves the Anthropic API; omit it to use a normal login. Presets for OpenRouter, NRP, ALCF and Argo, expiring tokens, mapping the model tiers to the provider's models, and changing or removing a provider are in [API Providers](#api-providers).

## The Launcher

```bash
claude-supervisor update              # this profile's pack, then offers claude update
claude-supervisor update --all        # every install in this launcher's prefix
claude-supervisor uninstall           # delete this profile
claude-supervisor status              # this profile's version and file states
claude-supervisor list                # every install in this launcher's prefix
claude-supervisor memory externalize|link|status  # keep this project's memory outside the repo (see Memory)
claude-supervisor critic enable|disable|status    # Codex as the reviewer (see Codex As Critic)
claude-supervisor --version           # pack and claude versions (or -v)
claude-supervisor -h                  # the launcher's own help (or --help, help)
```

The launcher handles `update`, `uninstall`, `status`, `list`, `memory`, `-v` and `-h` for its own profile, and `critic` through the install's Codex script. Anything else goes to `claude`, so `claude-supervisor --resume` works as usual. Use `./deploy` for other installs. Replace `supervisor` with your `--tag`.

- `update` updates this profile's pack from the branch it was installed from, then asks `Run claude update? [y/N]`, because a new pack can need a newer Claude Code. `--yes` answers yes; `--dry-run` shows what would change.
- `uninstall` deletes this profile (its dir with sessions, history, login and token, and its launcher). It asks you to type the tag to confirm; `--yes` skips that.
- Without a terminal, `uninstall` needs `--yes` (exit code 2 otherwise); `update` still runs and skips only the `claude update` question.
- If the install's copy of `deploy` (see Update) is missing, the launcher prints `claude-<tag>: <path> missing; run ./deploy install from your checkout` and exits 1.
- `--fable-is-opus` runs that session with Fable mapped to Opus; see Fable Or Opus.
- `--global` installs have no launcher; use the deploy tool (`./deploy memory --global <verb>` from a checkout).

## Update

Every install records itself in a registry and keeps a copy of `deploy` beside it, both in `<prefix>/state/claude-supervisor/`, so `update` does not need the checkout. Each `--prefix` has its own registry. The commands below use the default prefix.

```bash
~/.local/state/claude-supervisor/deploy update                # the default profile; or "$REPO/deploy" update
~/.local/state/claude-supervisor/deploy update --tag work     # another profile (--target DIR, or --global)
~/.local/state/claude-supervisor/deploy update --all --yes    # every registered install
~/.local/state/claude-supervisor/deploy list                  # what is registered
```

`list` shows each install's tag, target, version and branch, and whether its launcher exists.

`update` clones the recorded branch from the recorded remote and reinstalls with the install's recorded options, provider settings included. It needs git and network access, and it sees only what is pushed to that branch. `--all` updates every registered install without asking; `--dry-run` shows the changes; `update --from DIR --all` updates only the installs that follow DIR's branch.

If an install is newer than what `update` would install, `update` prints a WARNING naming both versions and asks `Continue with the update? [y/N]`. The default leaves the install unchanged. Without a terminal it needs `--yes` to continue.

An install with no recorded remote (the source was not a git checkout) errors; update it with `--from DIR`, where DIR is a checkout.

If the recorded branch is gone from the remote, `update` leaves that install unchanged and prints `STALE <target>: nothing to update; branch <b> is gone from <remote>; this install is stale. Remove it with: claude-<tag> uninstall (or ./deploy uninstall --tag <tag> --target <target>)`. Under `--all` the other installs still update. A network or auth failure is an error, not stale.

`status` appends `(MISMATCH: run ./deploy install from your checkout)` when the installed version differs from the checkout's. After an `update` the recorded source is a deleted clone, so `status` says `(source not available)`, which is not a mismatch; pass `--source "$REPO/pack"` to compare.

### Dev Worktree Install

To try a feature branch next to your normal install, give it its own worktree (in-repo, under `.claude/worktrees/`, which this repo ignores) and tag:

```bash
git -C "$REPO" worktree add .claude/worktrees/my-feature -b my-feature
"$REPO/.claude/worktrees/my-feature/deploy" install --tag supervisor-dev
claude-supervisor-dev            # runs the branch's pack
git -C "$REPO/.claude/worktrees/my-feature" push -u origin my-feature
claude-supervisor-dev update     # pulls the pushed my-feature branch
```

`update` follows the pushed branch, so push it first. The install's version is derived from the branch (such as `2.3+my-feature.2.g8b1d7de`), so unpushed commits make it newer than the pushed branch and `update` asks before downgrading it. To deploy unpushed edits, run `./deploy install --tag supervisor-dev` from the worktree. Once the branch is deleted from the remote, `update` reports the install as stale (exit code 3); remove it with `claude-supervisor-dev uninstall`.

## Fable Or Opus

Three agents (`supervisor`, `writer`, `scope-critic`) run on Fable, and `planner` and its `critic` join them when a plan is complex (see [Models And Cost](architecture.md#models-and-cost)) or when you ask for thorough planning. Fable is billed to usage credits on some plans. To run them on Opus for one session, start `claude-<tag> --fable-is-opus`. To do it for every session, set `ANTHROPIC_DEFAULT_FABLE_MODEL` in your shell profile (`export ANTHROPIC_DEFAULT_FABLE_MODEL=claude-opus-5-5`); the launcher respects it, and the flag overrides it. On a provider profile the flag maps Fable to the model you picked for the Opus tier (see [API Providers](#api-providers)).


`--global` installs have no launcher, so `install --global` prints a note and the agents run on Fable until you set the variable yourself, in a shell profile or in `~/.claude/settings.json`:

```bash
export ANTHROPIC_DEFAULT_FABLE_MODEL=claude-opus-5-5
```

```json
{ "env": { "ANTHROPIC_DEFAULT_FABLE_MODEL": "claude-opus-5-5" } }
```

A value in `~/.claude/settings.json` is copied into any profile created later, and there it applies to every session, `--fable-is-opus` or not.

## API Providers

A profile can run on an API provider instead of your Claude subscription: any endpoint that serves the Anthropic Messages API, with the provider's models mapped to the four pack tiers (Fable, Opus, Sonnet, Haiku). Install it into a profile of its own, with its own tag and launcher; the subscription profile stays as it is, and `--global` refuses the provider flags. Anthropic does not support Claude Code on non-Claude models, and how well a model follows the agents' tool calls varies by model, so try a candidate on a small task first.

### Presets

```bash
"$REPO/deploy" install --tag or --provider openrouter --token-file ~/openrouter.key
"$REPO/deploy" install --tag nrp --provider nrp --token-file ~/nrp.token
"$REPO/deploy" install --tag alcf --provider alcf
"$REPO/deploy" install --tag argo --provider argo --username NAME
```

A preset fills in the base URL, how the token is supplied and where the model list comes from. Install then asks for a model per tier on a terminal (see Model Tiers); without one it needs the four `--model-<tier>` flags. Argo is the exception: it ships default tiers.

- **OpenRouter**, `https://openrouter.ai/api`: a static key, created at https://openrouter.ai/keys. The list offers OpenRouter's models that support tool calling.
- **NRP**, `https://ellm.nrp-nautilus.io/anthropic`: a static token from https://nrp.ai/llmtoken.
- **ALCF**, `https://inference-api.alcf.anl.gov/resource_server/minerva/api` (the Minerva cluster): access tokens expire after 48 hours, so the preset uses the token helper `alcf-tokens get-token inference` instead of a static token. Install `alcf-tokens` and run `alcf-tokens login inference` once; when the helper prints no token, `install`, `update` and `doctor` fail with that login command. For Tara, add `--base-url https://inference-api.alcf.anl.gov/resource_server/tara/api`. The helper command and the model list follow ALCF's documentation and are not yet confirmed against the live service; when the list cannot be fetched, the picker takes typed model ids.
- **Argo** (Argonne), `https://apps.inside.anl.gov/argoapi`. The tiers default to `claude-opus-5-5` (Fable and Opus, since Argo has no Fable), `claude-sonnet-5-5` and `claude-haiku-5-5`, so no picker runs; `--model-<tier>` flags replace single tiers.
  1. Connect from inside ANL or over the VPN; Argo is not reachable from elsewhere.
  2. Pass `--username NAME`, your ANL domain username. Argo takes it in place of a token, so it is not secret and shows in `status`. Without it, install asks `ANL username [$USER]:` on a terminal; without a terminal it fails and names the flag.
  3. Optionally, to go through argo-proxy, run `argo-proxy serve` with the same username as `user:` in its `config.yaml`, and add `--base-url http://localhost:44497` (the proxy root, without `/v1`). The username helper, the tier defaults and the export below stay.

  The launcher exports `CLAUDE_CODE_AUTO_MODE_SERVER=0` because Argo does not support the auto mode server.

A static token (`--token-file PATH`, or `--token VALUE`, which leaves the value in your shell history) is copied to `<dir>/token` (mode 0600), and the launcher exports it as `ANTHROPIC_AUTH_TOKEN` with `ANTHROPIC_API_KEY` set empty, so a real Anthropic key in your environment never reaches the provider. A token helper (`--token-helper CMD`; the ALCF preset's default) goes into the profile's `settings.json` as `apiKeyHelper`, so Claude Code calls it and refreshes the token when it expires. The helper must print just the token on one line. An `apiKeyHelper` you set yourself is kept, with a warning. The token never appears in the manifest, `settings.json`, install output or `status`.

Any other provider that serves the Anthropic Messages API takes `--base-url URL` with one of the token flags, as under Token Provider. Given with `--provider`, `--base-url` replaces only the preset's URL.

### Model Tiers

A provider profile's launcher maps the four tiers to the provider's models (through `ANTHROPIC_DEFAULT_<TIER>_MODEL`) and uses the Opus-tier model as the main model; the agent files are unchanged. On a terminal, install asks for one model per tier, Fable first:

```
Pick a model per tier from openrouter: a number, an exact id, or text to filter by (? lists)
Fable-tier model:
```

Type `?` to list models, text to filter (`qwen`), or a number or an exact id to pick. From the second tier on, Enter repeats the previous pick, so a single-model provider takes one pick and three Enters. When the list cannot be fetched, install prints one WARNING and takes typed ids.

For scripts, or without a terminal, give every tier on the command line; `--yes` also skips the picker:

```bash
"$REPO/deploy" install --tag nrp --provider nrp --token-file ~/nrp.token \
  --model-fable <id> --model-opus <id> --model-sonnet <id> --model-haiku <id>
```

A preset, or any `--model-<tier>` flag, needs all four tiers. A re-install keeps the recorded ones, so a single flag changes one tier.

With `--base-url` and no preset, install asks `Map the model tiers to this provider's models? [y/N]` on a terminal. Declined, or without a terminal, the tiers stay unset, which suits a gateway that serves Claude model ids; once mapped, the all-or-nothing rule above applies.

On a provider profile, `--fable-is-opus` maps Fable to the Opus-tier model. An `ANTHROPIC_*` value, or Argo's `CLAUDE_CODE_AUTO_MODE_SERVER`, in the profile's `settings.json` `env` overrides the launcher: the first install leaves such keys out when it copies `~/.claude/settings.json`, and `doctor` warns about any added later.

### Changing Or Removing A Provider

A plain `install`, and `update`, keep the recorded provider, token or helper, and models. `status` prints `Provider:`, `Base URL:`, `Auth:` and one `Model <tier>:` line each; `doctor` checks the token file, the helper and the `env` block (see Doctor Checks). Re-run `install` with new flags to change part of it: a `--model-<tier>` flag replaces that tier, `--token-file` replaces the token or turns a helper profile into a static-token one (`--token-helper` does the reverse), and a different `--base-url` drops the recorded models, so the tiers are picked, or passed, again (the Argo preset's defaults apply instead). `--provider ''` or `--base-url ''` removes the whole provider config: the launcher goes back to the subscription form, `<dir>/token` is deleted and a managed `apiKeyHelper` is removed (one you set yourself is kept, with a warning); the profile then uses a normal login. `uninstall` deletes the token with the profile.

## Codex As Critic

An opt-in mode in which the lead's critic step runs OpenAI Codex CLI instead of the Claude `critic` subagent. Only the critic changes: `scope-critic` stays on Claude, and any failed Codex review falls back to the Claude critic for that round, automatically. It needs the `codex` CLI on `PATH` and a logged-in Codex account (`codex login`); `enable` checks both before it asks for consent.

### Consent, Cost, And Data Flow

- Codex reviews spend your OpenAI/ChatGPT quota.
- Repository content under the current directory, the review brief and the diff are sent to OpenAI.

`enable` prints this consent text and asks for a yes; without a terminal it needs `--yes`. Codex runs read-only and ephemeral.

Install adds one rule to `permissions.allow` in `settings.json` that allows the review script's `review` command, so Codex reviews never ask you for permission. `enable`, `disable` and `status` are not allowed, so turning Codex on from a session costs one prompt and no agent can do it unasked.

### Switching

```bash
./deploy critic enable [MODEL]       # also: disable, status; take --tag, --target or --global
claude-supervisor critic status      # the launcher forwards to the same script
/supervisor-config critic codex [model] | claude | status    # inside a session
```

No reinstall is needed. The mode lives in `supervisor-config.json`, next to `settings.json`, and a switch takes effect from the next task. `install` prints a hint to enable it when `codex` is on `PATH` and the mode is off.

### Models

The default is `gpt-6.1-sol` at effort `high`; `gpt-6-astra` is also verified. Per-domain overrides are edited by hand into `supervisor-config.json`; `enable` keeps them, but `disable` removes them, so set them again after a re-enable. The domains are `research`, `plan`, `code`, `prose` and `agent-definition`; each override is `claude` or an object with `model` and `effort`:

```json
{"critic": {"domains": {"prose": "claude", "plan": {"model": "gpt-6-astra", "effort": "xhigh"}}}}
```

### Fallback And Which Engine Reviewed

When Codex is off for a domain, missing, fails or times out, that round falls back to the Claude `critic`. The lead's report names the engine per round (`critic: codex gpt-6.1-sol high`, or `critic: claude (<reason>)`). `critic status` shows the backend, models, domain overrides, Codex login and whether the allow rule is present; `doctor` prints a `critic backend: claude|codex` row.

### Caveats

- Claude Code's own sandbox blocks OpenAI hosts unless they are allowlisted, and whether Codex's Seatbelt sandbox runs nested inside it is unconfirmed. If reviews fall back with a network or sandbox reason, check that first.
- Model IDs are account-specific. A wrong one makes every review fall back to Claude, with the reason in the lead's report; `doctor` and `critic status` show the login state.
- If the install path is reached through a symlink, the allow rule can miss and every review prompts. `critic status` prints the rule for the path it ran from; if the lead types the other form (literal or symlink-resolved), add that form to `permissions.allow` too.
- Install a branch's pack with that branch's own `deploy` (`<checkout>/deploy install --source <checkout>/pack`): an older `deploy` copies the pack but writes no review rule, so every Codex round prompts; `critic status` then shows `rule present: no`.
- Codex runs in a read-only sandbox and may not be able to run the tests itself (on macOS it can refuse a conda `python3`, and a Homebrew one may lack pytest); the lead has already run them, so a review note that tests were not independently run is expected.
- Reviews take from tens of seconds to several minutes; after 540 s the round falls back.

## Memory

```bash
claude-supervisor memory externalize [--root DIR] [--name N]
claude-supervisor memory link [DIR] [--root DIR] [--name N]
claude-supervisor memory status
```

Use this to keep a local memory store outside the repo, shared by all its worktrees ([local-memory.md](local-memory.md)). Run it inside a git project. `externalize` moves the project's `.supervisor/` and `CLAUDE.local.md` (or creates them) to `<root>/<name>/`, replaces them with absolute symlinks, and lists both in `.git/info/exclude`. `link` attaches a checkout, a linked worktree or a fresh machine to an existing external directory, and `status` reads without writing and exits 1 with a repair hint. The root is `$CLAUDE_SUPERVISOR_MEMORY_ROOT`, else `${XDG_DATA_HOME:-~/.local/share}/claude-supervisor/memory`.

`externalize` and `link` check everything before they write, are safe to repeat, and never overwrite or delete your files. Windows is not supported. Setup, git history for the memory, fresh machines, worktrees and moving back are covered there.

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
| Codex critic (only when `critic.backend` is `codex`) | FAIL | `codex` missing from `PATH` or not logged in; install it, run `codex login`, or run `critic disable` |
| Provider profile: `<dir>/token` missing or not mode 600 | FAIL | Re-run `./deploy install --tag <tag> --token-file PATH`, or `chmod 600` the file |
| Provider profile: token helper prints no token | FAIL | Log in again (ALCF: `alcf-tokens login inference`), or re-run `install` with a working `--token-helper` |
| `ANTHROPIC_*` or a preset-exported variable in `settings.json` `env` (provider profile) | WARN | It overrides the launcher's export; remove it |

The three environment variables are checked both in the shell environment and in the `env` block of the target's `settings.json`. Doctor exits 1 if any row is FAIL; WARN rows do not change the exit code.

## Uninstall

```bash
"$REPO/deploy" uninstall --dry-run
"$REPO/deploy" uninstall --yes
```

For a profile, uninstall deletes its dir, including sessions, history, login, and token, and its launcher. With `--global` it removes only the pack's files, after running `codex-critic disable` to drop the mode file, and it removes the review script's `settings.json` allow rule; a profile uninstall removes everything with its dir. Either way it removes the install's registry entry.

`uninstall --all` removes every install registered under the given `--prefix` after one confirmation that lists them. Entries whose target has no manifest are pruned from the registry.

For `--global`: uninstall removes the unmodified managed files and keeps the ones you edited; `--force` removes those as well. It restores your previous `agent` setting.

## Migrate

```bash
"$REPO/deploy" migrate
```

`migrate` moves a pack installed straight into `~/.claude` (see Older Installs) to the default profile, after one confirmation:

1. It finds the old install by its manifest in `~/.claude`: `.claude-supervisor-manifest.json`, or the older `.claude-agents-manifest.json` (lock `.claude-agents.lock`).
2. It copies the pack files you edited to a timestamped backup directory at the top level of `~/.claude`, removes all of the pack's files and its manifest, and restores the `agent` setting as `uninstall` does. `settings.json` is backed up first; nothing else in `~/.claude` is touched besides these backups.
3. It installs and registers the default profile and its launcher, as `install` does.
4. It checks that `~/.local/bin` is on `PATH`.

With no old install, it just installs. It removes edited pack files too, after the backup: a pack file left in `~/.claude` without its manifest is copied into the next new profile and refused as unmanaged. Plain `claude` then starts plain Claude Code.

## Older Installs

What changes with the version an install was made with; `status` prints the installed version.

- Before 1.19: run `"$REPO/deploy" install` once from the checkout. It renames an old manifest, registers the install, rewrites the launcher and records the branch. Before 1.10 every install went into `~/.claude`; `migrate` moves such an install to the default profile.
- Before 4.17 the launcher took `--fable`; it now strips the flag, prints a one-line notice on stderr and continues.
- Before 5.0 the trailer was `Co-Authored-By: Claude Supervisor`; install replaces it where install set it and leaves a value you set yourself alone.

## Exit Codes

- `0`: success.
- `1`: a file or settings step failed (see the output), a `doctor` row was FAIL, or a prompt was declined or aborted (Ctrl-D).
- `2`: a usage error, a failed source validation, a held lock, or an OS error such as an unreadable path.
- `3`: `update` found an install whose recorded branch is gone from its remote.

## Notes For Claude Running This

- Run the commands through Bash exactly as shown. Without a terminal, `uninstall`, `install --overwrite-local`, `uninstall --all`, `migrate` and `claude-<tag> uninstall` need `--yes`; `claude-<tag> update` needs it only to run `claude update`.
- If install reports kept local modifications or unmanaged collisions, show the user the list and ask before re-running with `--overwrite-local`.
- If doctor reports a FAIL, report it and its fix. Do not edit the user's shell profile (including the PATH line `install` prints) or environment variables without asking.
- Exit codes are listed under [Exit Codes](#exit-codes).
- If `status` shows `MISMATCH`, the installed pack is not the checkout's version: run `install`. `(source not available)` is not a mismatch; pass `--source "$REPO/pack"` to compare.

## Routing Check

For contributors: if you edit agent descriptions in your checkout, run the live routing check. The supervisor decides where each request goes from the agent descriptions it sees, so a reworded description can silently change routing. `tests/test_live_routing.py` guards against that: it asks the deployed supervisor to route 28 canonical requests without dispatching anything. The supervisor answers each with its mode, the agent, and the `model:` alias it would pass (`default` when none), and the test compares all three with the expected ones. The cases cover the quick specialists, a plain question, research, planning, implementation, writing and an escalation, plus the model tiers: the planner on its default and on Fable (a program, an open cross-module design, an unfamiliar domain, a request for thoroughness; never for plan annotation or checklist sync), the writer and the executor on Opus only for the work the routing rules name, and a stated target or an obvious bug fix going straight to the executor.

```bash
SUPERVISOR_LIVE_ROUTING=1 python3 -m pytest -q tests/test_live_routing.py -s
```

- It calls the model 28 times through `claude-supervisor`, against the deployed default profile. Run `./deploy install` first so it tests the pack you mean to test.
- It costs money. Each case is capped at $0.50 (hard maximum $14 for the run) and typically costs a few cents to tens of cents (expected about $4 to $8). The run prints the case count, the total cost and the model at the end. A case also fails if the supervisor needs more than two turns to answer.
- It is opt-in: a plain `python3 -m pytest -q` skips it. Run it after changing an agent description or the supervisor's routing rules.

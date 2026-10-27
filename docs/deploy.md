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

- Copies `pack/agents/*.md` to `<target>/agents/` and `pack/skills/*` to `<target>/skills/`. The target is a profile, `~/.config/claude-<tag>` (`--tag`, default `supervisor`; `--target DIR` sets another dir), or `~/.claude` with `--global`, which skips the first-install copy from `~/.claude` (below) and has no launcher. `$CLAUDE_CONFIG_DIR` is ignored.
- Records SHA-256 hashes in `<target>/.claude-supervisor-manifest.json`. Re-running `install` is the update path and is idempotent:

| Situation | Action |
|---|---|
| File not installed yet | copied |
| Installed and unmodified, source changed | updated |
| You edited the installed file | kept, with a warning (`--overwrite-local` backs it up as `<file>.bak-<timestamp>` and replaces it) |
| An unmanaged file with that name exists | refused, exit code 1 (`--overwrite-local` backs it up and replaces it) |
| File removed from the pack | deleted if unmodified, otherwise kept and handed over to you |

- Sets `"agent": "supervisor"` in `settings.json`. It backs up the file first, writes atomically, and keeps every other key. If you already have a different `agent`, the script leaves it alone unless you pass `--force-default-agent`. `--no-default-agent` skips this step (and restores your previous value if install had set it). `claude-supervisor --agent <other>` overrides the setting for a single session. A provider profile with a token helper also gets `apiKeyHelper` (see [API Providers](#api-providers)).
- In a profile (never with `--global`), also sets `attribution.commit` to `Co-Authored-By: Supervisor for Claude` in `settings.json`, so commits made by the agents carry that trailer instead of Claude Code's default. It also sets `attribution.pr` to `""` and `attribution.sessionUrl` to `false` ([docs](https://code.claude.com/docs/en/settings-reference#attribution-sessionurl)), so commits and PRs carry only the Supervisor for Claude trailer, with no session link and no "Generated with Claude Code" footer. Other keys are kept. Each sub-key is set only when absent; a value you set yourself (a different `commit` text, any `pr` or `sessionUrl`, or `attribution: false`) is left alone, and the install message says so. The manifest records which of them install set; deleting the profile on uninstall removes it with the rest.
- Validates every source agent and skill before writing anything, and holds a lock so two deploys cannot run at once.
- Records the checkout's current git branch next to the remote in the registry; `update` follows it. A detached HEAD records `main` and prints a one-line warning; a source that is not a git checkout records `main` silently. `status` prints `Remote: <url or none>` and `Branch: <branch>` from the registry, or `Remote: not registered`.
- Records the checkout's version as `pack_version` in the manifest and prints `Version: <version>`, with `(was <old>)` on an update (see Versions).
- On a profile's first install, copies from `~/.claude`: `settings.json` (without `agent`), `CLAUDE.md`, `commands/`, `output-styles/`, `keybindings.json`, and your own files in `agents/` and `skills/` (not `skills/.trash` or `skills/synced`). Plugins, logins, history, and sessions stay behind.
- Writes the launcher `<prefix>/bin/claude-<tag>` (`--prefix P`, default `~/.local`), which runs `claude` with `CLAUDE_CONFIG_DIR` set to the profile. The profile dir does not depend on the prefix. The manifest records the prefix, and `install` and `uninstall` refuse a different `--prefix` for an existing install (exit code 2, with the prefix to pass). Install also refuses a tag whose launcher path exists and was not written by the deploy.

### Versions

`VERSION`, the file next to `pack/`, holds the `main` version only; install derives the version it records from git. On `main` it is plain `X.y`, also when the tree is dirty. On any other branch, or a detached HEAD (label `detached`), it is `<VERSION at the merge-base with main>+<branch>.<commits ahead of main>.g<short sha>`, plus `.dirty` when the pack dir has uncommitted changes, for example `2.3+memory-v2.7.g8b1d7de`. In the branch name, characters other than letters, digits, `.` and `-` become `-`. The base is `origin/main`, else local `main`; with neither, the version is plain `X.y`. Nothing needs editing after a rebase. `status`, `list` and `--version` use the same derived version.

### Token Provider

```bash
"$REPO/deploy" install --tag work --base-url https://llm.example.com --token-file ~/work.token
```

Routes the profile through a proxy or gateway that serves the Anthropic API; omit it to use a normal login. Presets for OpenRouter, NRP and ALCF, expiring tokens, mapping the model tiers to the provider's models, and changing or removing a provider are in [API Providers](#api-providers).

## The Launcher

```bash
claude-supervisor update              # claude update, then this profile's pack
claude-supervisor update --all        # every install in this launcher's prefix
claude-supervisor uninstall           # delete this profile
claude-supervisor status              # this profile's version and file states
claude-supervisor list                # every install in this launcher's prefix
claude-supervisor --version           # pack and claude versions (or -v)
claude-supervisor -h                  # the launcher's own help (or --help, help)
```

For commands, the launcher checks only its first argument, after removing `--fable-is-opus` (see Fable Or Opus for where the flag may stand). `update`, `uninstall`, `status` and `list` run the deploy tool copy under the launcher's own prefix (`<prefix>/state/claude-supervisor/deploy`), always for this launcher's install: `--tag`, `--target`, `--prefix` and `--global` are refused with exit code 2 (use the deploy tool for other installs), and their help and usage errors name `claude-<tag>`. `-v`/`--version` and `-h`/`--help`/`help` are answered by the launcher itself. Everything else, including unknown flags, goes to `claude` unchanged, so `claude-supervisor -p update`, `claude-supervisor --resume` and `claude-supervisor doctor` (Claude Code's own) still reach `claude`. Replace `supervisor` with your `--tag`.

- `update` asks y/N, then runs `claude update` first, because a new pack can need a newer Claude Code, and then updates the pack from the remote and branch recorded at install, like `deploy update --tag <tag>`. If `claude update` fails, it says so and still updates the pack; the exit code is 1 if either step failed. `--yes` skips the question, and `--dry-run` shows what would change, including "would run claude update".
- `uninstall` deletes this profile (its dir with sessions, history, login and token, its launcher, and its registry entry). It asks you to type the tag to confirm; `--yes` skips that. `uninstall --all` is refused from a launcher; use the deploy tool's `uninstall --all`.
- Without a terminal, both need `--yes` (exit code 2 otherwise).
- If the tool copy is missing, the launcher prints `claude-<tag>: <path> missing; run ./deploy install from your checkout` and exits 1.
- `status` reports this install as `deploy status` does; when the recorded source dir is gone, it suggests `./deploy status --tag <tag> --source <checkout>/pack`, with `--target <dir>` added for an install made with `--target`, to compare.
- `-h` / `--help` / `help` prints the launcher's commands, its tag and config dir, and a note that `install` and `doctor` run from the checkout.
- `-v` / `--version` prints `claude-supervisor <installed pack version> (claude-<tag>, <config dir>)` and a `claude: <version>` line (`claude: not found` if it is missing).
- `--fable-is-opus` runs that session with Fable mapped to Opus; see Fable Or Opus.
- If `claude` is not on `PATH`, a session start prints `claude-<tag>: claude not found on PATH; install Claude Code, then retry` and exits 127.
- `--global` installs have no launcher; use the deploy tool.

## Update

Every install records itself in a registry and writes a copy of the deploy tool beside it, so `update` does not need the checkout. The commands below use the default prefix; add `--prefix P` for another.

```bash
~/.local/state/claude-supervisor/deploy update                # the default profile; or "$REPO/deploy" update
~/.local/state/claude-supervisor/deploy update --tag work     # another profile (--target DIR, or --global)
~/.local/state/claude-supervisor/deploy update --all --yes    # every registered install
~/.local/state/claude-supervisor/deploy list                  # what is registered
```

- Registry: `<prefix>/state/claude-supervisor/installs.json` (by default under `~/.local/state/claude-supervisor/`).
- Tool copy: `<prefix>/state/claude-supervisor/deploy`, with the version of the install that last wrote it beside it in `VERSION` (removed when the source has no `VERSION`).
- Installs are stand-alone: nothing an install runs depends on the source checkout existing or being unchanged, and version and update information come from what the install recorded. The registry file and tool copy stay after uninstall; only the install's entry is removed.
- Each prefix is independent: it has its own registry and tool copy, and `update` and `uninstall` (and `--all`) act on the registry of the `--prefix` you give.

`list [--prefix DIR]` shows each install in that prefix's registry: tag, target, installed version, branch, commit (short, with `-dirty` if the source was dirty), and whether the launcher exists (`yes`, `missing`, or `-` for `--global` or when there is no readable manifest). `./deploy --version` prints the checkout's derived pack version and the `claude:` line; the tool copy's `--version` (`~/.local/state/claude-supervisor/deploy --version`) prints the version recorded by the install that last wrote the tool copy, without the checkout.

`update` clones the branch recorded at install from the git remote recorded at install into a temp dir (shallow for `main`; full history for other branches, so the merge-base with `main` is available for the version) and reinstalls with each install's recorded options (prefix, `--no-default-agent`, and a provider profile's base URL, token or token helper, and tier models; see [API Providers](#api-providers)). It works without the checkout, but it needs git and network or ssh access, and it only sees what is pushed to that branch. `--all` groups installs by remote and branch and asks once before changing anything. `--yes` skips that question and `--dry-run` shows the changes. `update --from DIR --all` updates only the installs whose remote and branch match DIR's checkout.

If an install is newer than what `update` would install (main version first, then commits ahead), `update` prints a WARNING naming both versions and asks `Continue with the update? [y/N]`. The default is No: the install is left unchanged and the exit code is 1. Without a terminal it fails (exit code 2) unless `--yes` is passed, and `--dry-run` only warns.

An install with no recorded remote (the source was not a git checkout) errors; update it with `--from DIR`, where DIR is a checkout.

If the recorded branch is gone from the remote, `update` leaves that install unchanged and prints `STALE <target>: nothing to update; branch <b> is gone from <remote>; this install is stale. Remove it with: claude-<tag> uninstall (or ./deploy uninstall --tag <tag> --target <target>)` (a `--global` install says `./deploy uninstall --global`). Under `--all` the other installs still update, and the exit code is 3. A network or auth failure reaching the remote is an error (exit code 1), not stale.

`status` prints `Version: installed=<version>, source=<version>` and appends `(MISMATCH: run ./deploy install from your checkout)` when they differ. When the recorded source dir is gone or is no longer a valid pack and `--source` is not given, as after an update (the manifest names the deleted clone), it prints `Source: <dir> (not available; pass --source <checkout>/pack to compare)` and `Version: installed=<version> (source not available)` with no MISMATCH, and reports file states (ok, modified, missing) from the manifest alone. Pass `--source "$REPO/pack"` to compare versions.

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

Four agents (`supervisor`, `planner`, `writer`, `scope-critic`) are written for Fable, and `planner` also names `model: fable` when it dispatches `critic`. Deployed files always say `model: fable`, byte for byte as in `pack/`. Fable is billed to usage credits on some plans. By default the launcher leaves `ANTHROPIC_DEFAULT_FABLE_MODEL` alone: if it is unset, those agents and that dispatch override run on Fable; if your environment defines it (for example `export ANTHROPIC_DEFAULT_FABLE_MODEL=claude-opus-5-5` in a shell profile), that value is respected. `claude-<tag> ... --fable-is-opus` strips the flag and exports `ANTHROPIC_DEFAULT_FABLE_MODEL=claude-opus-5-5` for that session, overriding the environment. The flag counts in any position before a `--`, also next to a launcher command, where it has no effect; the other arguments reach `claude` in their order. On a provider profile the flag maps Fable to the model you picked for the Opus tier instead (see [API Providers](#api-providers)).

The value is a full model ID, the `OPUS_MODEL` constant in `deploy`. When a new Opus ships, update the constant and re-run `install` to regenerate the launchers.

`--global` installs have no launcher, so `install --global` prints a note and the agents run on Fable until you set the variable yourself, in a shell profile or in `~/.claude/settings.json`:

```bash
export ANTHROPIC_DEFAULT_FABLE_MODEL=claude-opus-5-5
```

```json
{ "env": { "ANTHROPIC_DEFAULT_FABLE_MODEL": "claude-opus-5-5" } }
```

A profile created later copies `~/.claude/settings.json`, and there a settings value applies to every session, whatever the shell environment or `--fable-is-opus` say. Setting the variable in your shell profile also reaches the launchers of existing profiles.

## API Providers

A profile can run on an API provider instead of your Claude subscription: any endpoint that serves the Anthropic Messages API, with the provider's models mapped to the four pack tiers (Fable, Opus, Sonnet, Haiku). Install it into a profile of its own, with its own tag and launcher; the subscription profile stays as it is, and `--global` refuses the provider flags. Anthropic does not support Claude Code on non-Claude models, and how well a model follows the agents' tool calls varies by model, so try a candidate on a small task first.

### Presets

```bash
"$REPO/deploy" install --tag or --provider openrouter --token-file ~/openrouter.key
"$REPO/deploy" install --tag nrp --provider nrp --token-file ~/nrp.token
"$REPO/deploy" install --tag alcf --provider alcf
```

A preset fills in the base URL, how the token is supplied and where the model list comes from. Install then asks for a model per tier on a terminal (see Model Tiers); without one it needs the four `--model-<tier>` flags.

- **OpenRouter**, `https://openrouter.ai/api`: a static key, created at https://openrouter.ai/keys. The list offers OpenRouter's models that support tool calling.
- **NRP**, `https://ellm.nrp-nautilus.io/anthropic`: a static token from https://nrp.ai/llmtoken.
- **ALCF**, `https://inference-api.alcf.anl.gov/resource_server/minerva/api` (the Minerva cluster): access tokens expire after 48 hours, so the preset uses the token helper `alcf-tokens get-token inference` instead of a static token. Install `alcf-tokens` and run `alcf-tokens login inference` once. `install`, `update` and `doctor` run the helper once each and fail with that login command when it prints no token. For Tara, add `--base-url https://inference-api.alcf.anl.gov/resource_server/tara/api`. ALCF's Claude Code recipe names only Minerva and Tara; Sophia and Metis would need a bridge outside this tool. The helper command and the model list at `<base URL>/v1/models` follow ALCF's documentation and are not yet confirmed against the live service; when the list cannot be fetched, the picker takes typed model ids.

A static token (`--token-file PATH`, or `--token VALUE`, which leaves the value in your shell history) is copied to `<dir>/token` (mode 0600), and the launcher exports it as `ANTHROPIC_AUTH_TOKEN` with `ANTHROPIC_API_KEY` set empty, so a real Anthropic key in your environment never reaches the provider. A token helper (`--token-helper CMD` for any provider; the ALCF preset's default) goes into the profile's `settings.json` as `apiKeyHelper`, with the command's program as an absolute path, and the launcher unsets `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY`, so Claude Code calls the helper and refreshes the token when it expires. The helper must exit 0 and print just the token on one line. Install sets `apiKeyHelper` when the key is absent or install set it before; a value you set yourself is kept, with a warning. Neither the token nor the helper's output ever appears in the manifest, `settings.json`, install output or `status`.

Any other provider that serves the Anthropic Messages API takes `--base-url URL` with one of the token flags, as under Token Provider. Given with `--provider`, `--base-url` replaces only the preset's URL.

### Model Tiers

Claude Code resolves the `fable`, `opus`, `sonnet` and `haiku` aliases in the agent files through `ANTHROPIC_DEFAULT_<TIER>_MODEL`, so a provider profile's launcher exports those four variables with the provider's models, plus `ANTHROPIC_MODEL` (the main model) as the Opus-tier model; the deployed agent files are unchanged. On a terminal, install asks for one model per tier, Fable first:

```
Pick a model per tier from openrouter: a number, an exact id, or text to filter by (? lists)
Fable-tier model:
```

`?` or an empty answer lists the first 30 models, with the context length when the provider reports it; other text filters the list (`qwen`); a number picks from the last list shown; an exact id picks it. From the second tier on, an empty answer repeats the previous pick, so a single-model provider takes one pick and three Enters. An id that is not in the list asks `is not in the list; use it anyway?`. When the list cannot be fetched (no network, or a token the provider refuses), install prints one WARNING and takes typed ids.

For scripts, or without a terminal, give every tier on the command line; `--yes` also skips the picker:

```bash
"$REPO/deploy" install --tag nrp --provider nrp --token-file ~/nrp.token \
  --model-fable <id> --model-opus <id> --model-sonnet <id> --model-haiku <id>
```

A preset, or any `--model-<tier>` flag, needs all four tiers. A re-install keeps the recorded ones, so a single flag changes one tier; a tier that is still missing without a terminal is an error listing the flags to pass, under `--dry-run` too. The list is fetched only when the picker runs, so scripted installs and `update` never fetch it; when it runs, a model given by flag that the list does not contain gets one WARNING.

With `--base-url` and no preset, install asks `Map the model tiers to this provider's models? [y/N]` on a terminal. Declined, or without a terminal, the tiers stay unset, which suits a gateway that serves Claude model ids; once mapped, the all-or-nothing rule above applies.

On a provider profile, `--fable-is-opus` maps Fable to the Opus-tier model. An `ANTHROPIC_*` value in the profile's `settings.json` `env` overrides the launcher: a provider profile's first install leaves such keys (and `apiKeyHelper`) out when it copies `~/.claude/settings.json`, and `doctor` warns about any added later.

### Changing Or Removing A Provider

A plain `install`, and `update`, keep the recorded provider, token or helper, and models. `status` prints `Provider:`, `Base URL:`, `Auth:` and one `Model <tier>:` line each; `doctor` checks the token file, the helper and the `env` block (see Doctor Checks). Re-run `install` with new flags to change part of it: a `--model-<tier>` flag replaces that tier, `--token-file` replaces the token or turns a helper profile into a static-token one (`--token-helper` does the reverse), and a different `--base-url` drops the recorded models, so the tiers are picked, or passed, again. `--provider ''` or `--base-url ''` removes the whole provider config: the launcher goes back to the subscription form, `<dir>/token` is deleted and a managed `apiKeyHelper` is removed (one you set yourself is kept, with a warning); the profile then uses a normal login. `uninstall` deletes the token with the profile.

## Codex As Critic

An opt-in mode in which the lead's critic step runs OpenAI Codex CLI instead of the Claude `critic` subagent. Only the critic changes: `scope-critic` stays on Claude, and any failed Codex review falls back to the Claude critic for that round, automatically. It needs the `codex` CLI on `PATH` and a logged-in Codex account (`codex login`); `enable` checks both before it asks for consent.

### Consent, Cost, And Data Flow

- Codex reviews spend your OpenAI/ChatGPT quota.
- Repository content under the current directory, the review brief and the diff are sent to OpenAI.

`enable` prints this consent text and asks for a yes; without a terminal it needs `--yes`. Codex runs read-only and ephemeral.

Every install (profile, `--global` or `--target`) adds one permission rule for its own read-only review script to `permissions.allow` in the install's `settings.json`: `Bash(<abs script path> review *)`, where the path is the installed `skills/supervisor-config/scripts/codex-critic` under the resolved install dir. The rule is added when absent, so `install` and `update` keep or restore it; `uninstall` removes it (a profile uninstall, with the dir). The rule covers only `review`, so the lead's probe and review calls never prompt, in either mode; `enable`, `disable` and `status` are not covered, so an in-session enable costs one permission prompt by design and no agent can turn Codex on unasked. `enable` and `disable` never touch `settings.json`.

### Switching

```bash
./deploy critic enable [MODEL]       # also: disable, status; take --tag, --target or --global
claude-supervisor critic status      # the launcher forwards to the same script
/supervisor-config critic codex [model] | claude | status    # inside a session
```

No reinstall is needed. The mode lives in `supervisor-config.json` in the install's config dir, next to `settings.json`. The lead probes the mode once per task, so a switch takes effect from the next task. `install` prints a hint to enable it when `codex` is on `PATH` and the mode is off. A global uninstall runs `disable` first.

### Models

The default is `gpt-6.1-sol` at effort `high`; `gpt-6-astra` is also verified. Per-domain overrides are edited by hand into `supervisor-config.json`; `enable` keeps them. A domain is `claude` or an object with `model` and `effort`:

```json
{"critic": {"domains": {"prose": "claude", "plan": {"model": "gpt-6-astra", "effort": "xhigh"}}}}
```

### Fallback And Which Engine Reviewed

When Codex is off for a domain, missing, times out, exits non-zero, writes nothing or returns a malformed block, the script prints `NO_CODEX` and the reason on stderr, and the lead dispatches the Claude `critic`. In the transcript the lead first makes one Bash call per task described `critic: check review backend` (`review --probe`, which prints `claude` or `codex <model> <effort>`, covered by the same rule); in Claude mode that is the only extra call and the `critic` launch follows as before. In Codex mode each round is a Bash call described `critic → codex <model> <effort>, round <n>` instead of a `critic` launch. A successful review ends with a `backend: codex <model> <effort>` line. The lead's report names the engine per round (`critic: codex gpt-6.1-sol high`, or `critic: claude (<reason>)`). `critic status` shows the backend, models, domain overrides, Codex login and whether the allow rule is present. `doctor` always prints a `critic backend: claude|codex` row.

### Caveats

- Claude Code's own sandbox blocks OpenAI hosts unless they are allowlisted, and whether Codex's Seatbelt sandbox runs nested inside it is unconfirmed. If reviews fall back with a network or sandbox reason, check that first.
- Model IDs are account-specific. A wrong one makes `codex` exit non-zero, so the review falls back with the reason on stderr. `doctor` and `critic status` show the login state.
- If the install path is reached through a symlink, the allow rule can miss and every review prompts. `critic status` prints the rule for the path it ran from; if the lead types the other form (literal or symlink-resolved), add that form to `permissions.allow` too.
- Install a branch's pack with that branch's own `deploy` (`<checkout>/deploy install --source <checkout>/pack`): an older `deploy` copies the pack but writes no review rule, so every Codex round prompts; `critic status` then shows `rule present: no`.
- Codex runs tests only through an interpreter its read-only sandbox may execute. On macOS the sandbox can refuse a conda `python3`, and a Homebrew one may lack pytest, so a Codex review may report that tests were not independently run.
- Codex's severities tend to run hot; `scope-critic`'s ruling is the calibrating layer.
- Reviews take from tens of seconds to several minutes. The script stops Codex after 540 s (`review --timeout SECS`) and falls back.

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
| `ANTHROPIC_*` in `settings.json` `env` (provider profile) | WARN | It overrides the launcher's export; remove it |

The three environment variables are checked both in the shell environment and in the `env` block of the target's `settings.json`. Doctor exits 1 if any row is FAIL; WARN rows do not change the exit code.

## Uninstall

```bash
"$REPO/deploy" uninstall --dry-run
"$REPO/deploy" uninstall --yes
```

For a profile, uninstall deletes its dir, including sessions, history, login, and token, and its launcher. With `--global` it removes only the pack's files, after running `codex-critic disable` to drop the mode file, and it removes the review script's `settings.json` allow rule; a profile uninstall removes everything with its dir. Either way it removes the install's registry entry.

`uninstall --all` removes every install registered under the given `--prefix` after one confirmation that lists them. Entries whose target has no manifest are pruned from the registry.

Uninstall removes the unmodified managed files and keeps the ones you edited; `--force` removes those as well. It restores your previous `agent` setting.

## Migrate

```bash
"$REPO/deploy" migrate
```

`migrate` moves a pack installed straight into `~/.claude` (see Older Installs) to the default profile, after one confirmation:

1. It finds the old install by its manifest in `~/.claude`: `.claude-supervisor-manifest.json`, or the older `.claude-agents-manifest.json` (lock `.claude-agents.lock`).
2. It copies the pack files you edited to a timestamped backup directory at the top level of `~/.claude`, removes all of the pack's files and its manifest, and restores the `agent` setting as `uninstall` does. `settings.json` is backed up first; nothing else in `~/.claude` is touched besides these backups.
3. It installs and registers the default profile and its launcher, as `install` does.
4. It checks that `~/.local/bin` is on `PATH`.

With no old install, it just installs. It removes edited pack files too, after the backup: a pack file left in `~/.claude` without its manifest is seeded into the next new profile and refused as unmanaged. Plain `claude` then starts plain Claude Code.

## Older Installs

What changes with the version an install was made with; `status` prints the installed version.

- Before 1.0 the manifest recorded no version; `status` shows `installed=not recorded` until the next install.
- Before 1.6 the manifest was `.claude-agents-manifest.json` (lock `.claude-agents.lock`). `status` still recognizes it and says so; the next `install` renames it.
- Before 1.10 every install went into `~/.claude`, where `--global` still installs; `migrate` moves such an install to the default profile.
- Before 1.12 installs were not registered, and before 1.13 launchers had no `update` or `uninstall` subcommands. Run `"$REPO/deploy" install` once from the checkout; it registers the install and rewrites the launcher.
- Global installs made before 1.14 had the agent files rewritten to `model: opus`; the next plain `install` restores `model: fable` without `--overwrite-local`.
- Registry entries from before 1.19 record no branch and count as `main`.
- Before 4.17 the launcher took `--fable`; it now strips the flag, prints a one-line notice on stderr and continues.
- Before 5.0 the trailer was `Co-Authored-By: Claude Supervisor`; install replaces it where install set it and leaves a value you set yourself alone.

## Notes For Claude Running This

- Run the commands through Bash exactly as shown. Without a terminal, `uninstall`, `install --overwrite-local`, `update --all`, `uninstall --all`, `migrate`, `claude-<tag> update` and `claude-<tag> uninstall` need `--yes`.
- If install reports kept local modifications or unmanaged collisions, show the user the list and ask before re-running with `--overwrite-local`.
- If doctor reports a FAIL, report it and its fix. Do not edit the user's shell profile (including the PATH line `install` prints) or environment variables without asking.
- Exit codes: 0 means success, 1 means a file or settings step failed (see the output), a `doctor` row was FAIL, or a prompt was aborted (declined or Ctrl-D), 2 means a usage error, a failed source validation, a held lock, or an OS error such as an unreadable path, and 3 means `update` found an install whose recorded branch is gone from its remote.
- If `status` shows `MISMATCH`, the installed pack is not the checkout's version: run `install`. `(source not available)` is not a mismatch; pass `--source "$REPO/pack"` to compare.

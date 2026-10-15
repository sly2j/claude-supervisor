# Deploying claude-agents

This runbook is for a human or for Claude asked to "deploy claude-agents". It works on macOS and Linux and needs only `python3` (3.9 or newer) and Claude Code 2.1.293 or newer.

## Steps

```bash
# first time (needs Argonne network or VPN):
git clone git@eicweb.phy.anl.gov:mep-agents/claude-agents.git ~/Work/claude-agents
REPO=~/Work/claude-agents
cd "$REPO" && git pull               # when updating

"$REPO/scripts/deploy" doctor        # preflight: python, claude version, env overrides (warns "not installed yet" on a fresh machine)
"$REPO/scripts/deploy" install --dry-run
"$REPO/scripts/deploy" install       # add --fable yes|no to skip detection (see Fable Or Opus)
"$REPO/scripts/deploy" status
"$REPO/scripts/deploy" doctor        # should now report no FAIL
```

Start a new Claude Code session afterwards. The session runs as `supervisor` because of `"agent": "supervisor"` in `~/.claude/settings.json`. Type `/agents` to see the installed agents.

## What Install Does

- Copies `pack/agents/*.md` to `<target>/agents/` and `pack/skills/*` to `<target>/skills/`. The target is `--target`, else `$CLAUDE_CONFIG_DIR`, else `~/.claude`.
- Records SHA-256 hashes in `<target>/.claude-agents-manifest.json`. Re-running `install` is the update path and is idempotent:

| Situation | Action |
|---|---|
| File not installed yet | copied |
| Installed and unmodified, source changed | updated |
| You edited the installed file | kept, with a warning (`--overwrite-local` backs it up as `<file>.bak-<timestamp>` and replaces it) |
| A file with that name exists that the pack does not manage | refused, exit code 1 (`--overwrite-local` backs it up and replaces it) |
| File removed from the pack | deleted if unmodified, otherwise kept and handed over to you |

- Sets `"agent": "supervisor"` in `settings.json`. It backs up the file first, writes atomically, and keeps every other key. If you already have a different `agent`, the script leaves it alone unless you pass `--force-default-agent`. `--no-default-agent` skips this step (and restores your previous value if the pack had set it). Start the supervisor with `claude --agent supervisor`. `claude --agent <other>` overrides the setting for a single session.
- Validates every source agent and skill before writing anything, and holds a lock so two deploys cannot run at once.
- Records the checkout's `VERSION` (the file next to `pack/`) as `pack_version` in the manifest and prints `Version: 1.x`, with `(was 1.y)` on an update. `status` prints `Version: installed=1.x, source=1.y` and appends `(MISMATCH: run scripts/deploy install)` when they differ. Manifests from before versioning show `installed=not recorded` until the next install.

## Fable Or Opus

Three agents (`supervisor`, `planner`, `scope-critic`) are written for Fable, and `planner` and `writer` also name `model: fable` in their dispatch instructions. Not every plan includes Fable, so `install` takes `--fable {auto,yes,no}`:

| Flag | Effect |
|---|---|
| `--fable yes` | Deploy the source verbatim, on Fable |
| `--fable no` | Deploy those agents and dispatch overrides as `opus` |
| `--fable auto` | Detect from your account (the default when nothing is saved) |

Detection runs `claude auth status --json` and reads your seat tier from `~/.claude.json` (or `$CLAUDE_CONFIG_DIR/.claude.json`). It makes no network or model requests.

| Account | Result |
|---|---|
| Max, or a premium Team or Enterprise seat | Fable |
| Pro, Free, a standard Team or Enterprise seat | Opus |
| Bedrock, Vertex, or Foundry | Opus |
| Any detection failure, including no `claude` on `PATH` | Opus |
| API key, or an unclear case (for example an unknown seat tier) | Asks once |

When Fable is off, only the agents under `agents/` change. Skills and the source in `pack/` stay as they are, so `pack/` always names Fable.

The choice is saved in the manifest. Later installs reuse it without asking, and `status` prints a `Fable:` line. To change it, re-run `install --fable yes`, `--fable no`, or `--fable auto` (which detects again). Without a terminal, or with `--yes`, an unclear detection defaults to Opus and says so.

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
"$REPO/scripts/deploy" uninstall --dry-run
"$REPO/scripts/deploy" uninstall --yes
```

Uninstall removes the unmodified managed files and keeps the ones you edited; `--force` removes those as well. It restores your previous `agent` setting.

## Notes For Claude Running This

- Run the commands through Bash exactly as shown. Without a terminal, `uninstall` and `install --overwrite-local` need `--yes`.
- If install reports kept local modifications or unmanaged collisions, show the user the list and ask before re-running with `--overwrite-local`.
- Bash has no terminal, so an unclear Fable detection defaults to Opus and says so in the `Fable:` line. Relay that to the user and offer `install --fable yes`.
- If doctor reports a FAIL, report it and its fix. Do not edit the user's shell profile or environment variables without asking.
- Exit codes: 0 means success, 1 means a file or settings step failed (see the output), and 2 means a usage error, a failed source validation, or a held lock.
- If `status` shows `MISMATCH`, the installed pack is not the checkout's version: run `install`.

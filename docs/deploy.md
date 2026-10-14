# Deploying claude-agents

This runbook is for a human or for Claude asked to "deploy claude-agents". It works on macOS and Linux and needs only `python3` (3.9 or newer) and Claude Code 2.1.293 or newer.

## Steps

```bash
REPO=/path/to/claude-agents          # this repo
cd "$REPO" && git pull               # when updating

"$REPO/scripts/deploy" doctor        # preflight: python, claude version, env overrides
"$REPO/scripts/deploy" install --dry-run
"$REPO/scripts/deploy" install
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
- If doctor reports a FAIL, report it and its fix. Do not edit the user's shell profile or environment variables without asking.
- Exit codes: 0 means success, 1 means a file or settings step failed (see the output), and 2 means a usage error, a failed source validation, or a held lock.

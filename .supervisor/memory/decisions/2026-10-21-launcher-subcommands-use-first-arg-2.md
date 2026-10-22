---
domain: code
summary: Launcher subcommands dispatch on the first argument after `--fable` is removed, run the prefix's tool copy, and update runs claude update first
affects: [deploy, docs/deploy.md, README.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#decisions
supersedes: .supervisor/archive/memory/decisions/2026-10-21-launcher-subcommands-use-first-arg.md
---
A `claude-<tag>` launcher looks at its first argument once every `--fable` before a `--` has been removed. `update`, `uninstall`, `list` and (since 3.3) `status` run the deploy tool copy under the launcher's own prefix (`<prefix>/state/claude-supervisor/deploy`) as `deploy --launcher PREFIX TAG TARGET <command> ...`; a user's `--tag`, `--target`, `--prefix` or `--global` is refused with exit 2 (until 3.3 they were appended last and silently ignored), and the tool copy still accepts the old appended form, because launchers written by older installs share it. Help and errors name `claude-<tag>`. When `claude-<tag> status` cannot find the recorded source dir, it prints `run ./deploy status --tag <tag> [--target <target>] --source <checkout>/pack to compare` (since 3.4); `--target` appears only when the target differs from ~/.config/claude-<tag>. `-v/--version` and `-h/--help/help` are answered by the launcher itself; everything else, unknown flags included, goes to `claude` unchanged. Before the subcommands existed, `claude-<tag> uninstall` sent the prompt "uninstall" to claude; `update` already meant `claude update`, and the new `update` keeps that meaning and adds the pack update. The dispatch is not generalised beyond these commands.

Decided behaviour under `--launcher`:
- `update` runs `claude update` first, because a new pack can need a newer Claude Code (doctor's minimum version). If it fails, report it, still update the pack, and exit 1 if either step failed. The deploy call runs before `CLAUDE_CONFIG_DIR` is exported, so `claude update` sees the user's normal environment. `update --all` replaces the tag/target selection.
- `update` asks y/N through the normal confirm prompt. `uninstall` instead requires typing the sandbox tag, because it deletes sessions, history and login. `--yes` skips either prompt; with no terminal both refuse with exit 2.
- `uninstall --all` is refused from a launcher (use the deploy tool).

`-h`/`--help` and `--version` stay first-argument only (3.2): claude has subcommands with their own help (`claude-<tag> mcp --help`), which an anywhere-match would hide. The owner asked (2026-10-22) that flags not depend on position; `--fable`, the launcher's only own session flag, now counts anywhere.

Reach: product; stated in deploy:49 (LAUNCHER_COMMANDS), deploy:87 (dispatch) and deploy:978 (status hint), and in docs/deploy.md:77 and :83.

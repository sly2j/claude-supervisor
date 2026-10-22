---
domain: code
summary: Launcher subcommands dispatch on the first argument only, run the prefix's tool copy, and update runs claude update first
affects: [deploy, docs/deploy.md, README.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#decisions
supersedes:
---
A `claude-<tag>` launcher looks only at its first argument. `update`, `uninstall` and `list` run the deploy tool copy under the launcher's own prefix (`<prefix>/state/claude-supervisor/deploy`): `update` and `uninstall` run with `--prefix`, `--tag`, `--target` and `--launcher` appended last (so a user's own values of those flags are ignored), while `list` gets only `--prefix`; `--version` and `-h/--help` are answered by the launcher itself; everything else except `--fable` (anywhere before a `--` since 3.2, see the Fable remap entry), unknown flags included, goes to `claude` unchanged. Before the subcommands existed, `claude-<tag> uninstall` sent the prompt "uninstall" to claude; `update` already meant `claude update`, and the new `update` keeps that meaning and adds the pack update. The dispatch is not generalised beyond these commands.

Decided behaviour under `--launcher`:
- `update` runs `claude update` first, because a new pack can need a newer Claude Code (doctor's minimum version). If it fails, report it, still update the pack, and exit 1 if either step failed. The deploy call runs before `CLAUDE_CONFIG_DIR` is exported, so `claude update` sees the user's normal environment. `update --all` replaces the tag/target selection.
- `update` asks y/N through the normal confirm prompt. `uninstall` instead requires typing the sandbox tag, because it deletes sessions, history and login. `--yes` skips either prompt; with no terminal both refuse with exit 2.
- `uninstall --all` is refused from a launcher (use the deploy tool).

Reach: product; stated in deploy:80.

`-h`/`--help` and `--version` stay first-argument only (3.2): claude has subcommands with their
own help (`claude-<tag> mcp --help`), which an anywhere-match would hide. The owner asked
(2026-10-22) that flags not depend on position; `--fable`, the launcher's only own session flag,
now counts anywhere.

---
domain: code
summary: --prefix scopes the launcher, registry and tool copy; installs under different prefixes are independent
affects: [deploy, docs/deploy.md, README.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#decisions
supersedes:
---
`--prefix P` (default `~/.local`, a common flag that may combine with `--global`) puts launchers in `P/bin/claude-<tag>` and the registry and tool copy in `P/state/claude-supervisor/`. It replaced the earlier `--bin-dir`, which was removed with no shim. Sandbox config dirs do not depend on the prefix (`~/.config/claude-<tag>` or `--target`).

Installs under different prefixes are independent: each prefix has its own registry and tool copy, `update`, `uninstall`, `list` and their `--all` forms act on the registry of the prefix given, and uninstalling `--all` under one prefix leaves another prefix's installs and registry untouched. The manifest records the prefix. `install` and single-target `uninstall` refuse with exit 2 when the existing manifest records a different one (`<target> was installed with --prefix <recorded>; pass --prefix <recorded>`), before anything is written, dry run included; a manifest with no `prefix` key counts as `~/.local`; under `uninstall --all` the entry is reported as an error and skipped. `update` replays the recorded prefix. Why: tests and dev worktrees need a place that does not touch the user's real install, and a recorded launcher path alone could not be recomputed for a custom location.

Reach: product; stated in deploy:222.

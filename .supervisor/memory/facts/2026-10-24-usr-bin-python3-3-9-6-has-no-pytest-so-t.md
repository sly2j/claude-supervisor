---
domain: process
summary: /usr/bin/python3 (3.9.6) has no pytest, so the 3.9 check of deploy is a py_compile, a help run and a dry-run install
affects: [deploy, CLAUDE.md]
verified: 2026-10-29
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#risks-and-compatibility
supersedes: .supervisor/archive/memory/facts/2026-10-21-usr-bin-python3-has-no-pytest-check-3.md
---
`deploy` must run on macOS's `/usr/bin/python3` (3.9.6), which has no pytest, so the suite cannot run under it and no test covers 3.9 syntax. The check for each change to `deploy` is:
- `/usr/bin/python3 -m py_compile deploy` succeeds,
- `/usr/bin/python3 ./deploy --help` exits 0,
- `HOME=$(mktemp -d) /usr/bin/python3 ./deploy install --dry-run --tag t` exits 0 (a fresh HOME keeps it off the real `~/.claude` and `~/.local`).
The installed tool copy and the launcher subcommands run under whatever `python3` is first on `PATH`, so they also run under 3.9 on macOS.

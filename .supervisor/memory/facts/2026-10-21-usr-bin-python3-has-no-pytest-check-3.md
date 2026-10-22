---
domain: process
summary: /usr/bin/python3 (3.9.6) has no pytest, so the 3.9 check of deploy is a py_compile, a help run and a dry-run install
affects: [deploy, CLAUDE.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#risks-and-compatibility
supersedes:
---
`deploy` must run on macOS's `/usr/bin/python3` (3.9.6), but that interpreter has no pytest (`import pytest` fails, re-checked 2026-10-21), so the test suite cannot run under it and no test covers 3.9 syntax. The check done for each change to `deploy` is therefore:
- `/usr/bin/python3 -m py_compile deploy` succeeds (REVIEW.md:7),
- `/usr/bin/python3 ./deploy --help` exits 0, and
- `HOME=$(mktemp -d) /usr/bin/python3 ./deploy install --dry-run --tag t` exits 0 (a fresh HOME keeps it away from the real `~/.claude` and `~/.local`).

It matters beyond import errors: the installed tool copy and the launcher subcommands run under whatever `python3` is first on `PATH`, and the launcher tests' `PATH=<tmp>/bin:/usr/bin:/bin` also run the copy under 3.9 on macOS.

Reach: repo work.

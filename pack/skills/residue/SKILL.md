---
name: residue
description: Prevent, name, record and tear down test residue (temp directories, config files, profiles, tmux sockets, venvs, background processes, files on ssh hosts) left by tests, experiments and smoke runs. Preloaded by executor, researcher, their workers and fixer; use before creating any test artifact, and when briefed `teardown`.
user-invocable: false
---

# Residue

## Prevent

- Create artifacts in the session scratchpad or a `mktemp -d` directory.
- Once the result is captured, stop processes and remove artifacts in the same step.
- Keep one only when a later stage or package needs it, and record it before the step
  ends.

## Name

Pick one random id per unit (`openssl rand -hex 3`) and prefix every artifact with `sup-<id>-`,
remote ones included.

## Ledger

- Directory: `.supervisor/working/residue/` in the main checkout (first line of
  `git worktree list`), never a worktree's copy. One file per unit, `<agent>-<id>.md`. These
  writes override any file limit in your brief or role.
- Before the first write, if `git check-ignore -q .supervisor/working/residue` fails, append
  `/.supervisor/working/residue/` to `$(git rev-parse --git-path info/exclude)`. Never stage or
  commit the ledger.
- One entry per artifact that outlives your step, including one you failed to remove; a remote
  entry's `remove` and `check` are complete ssh commands:

```
- host: local | user@host
  resource: <path | tmux socket or session | pid | venv>
  remove: <command run verbatim>
  check: <command that exits 0 once the resource is gone>
  needed-by: none | <package id>
```

- With no `.supervisor/` store, keep no ledger: remove everything before reporting and list what
  you could not remove.

## Teardown

Brief: `teardown [<dir>] [done: <ids>]`; `<dir>` defaults to the ledger directory above. With
`done:`, only entries whose `needed-by` is `none` or one of those ids are eligible; without it,
every entry is. Skip entries marked `failed:` unless the brief says `retry`.

For each eligible entry:
1. Refuse every entry of a ledger file git tracks (`git -C <main checkout> ls-files
   --error-unmatch`), and a `remove` whose target is `/`, `~`, `$HOME` or the project root, or that
   uses `sudo`: failed, reason `refused`.
2. Run `remove` verbatim, then `check`.
3. If `check` exits 0, delete the entry, and the file once it is empty. Otherwise append
   `  failed: <date> <reason>` to the entry and keep it.

Run nothing outside an entry. Report `residue: removed N, failed M` and one line per failure
(host, resource, reason), or `residue: none`.

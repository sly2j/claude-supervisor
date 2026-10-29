# Externalized Store

A project's `.supervisor` (and `CLAUDE.local.md`) may be a symlink into a directory outside the
repo, often inside another git repo that holds the memory.

## Detect

- `[ -L .supervisor ]` means the store is externalized.
- `git -C "$(readlink -f .supervisor)" rev-parse --show-toplevel` differing from the project
  toplevel means the target lies in another git repo (`<repo>`).

## Worktree cut

When the executor cuts a worktree, link the store in so every worktree shares it. For each of
`.supervisor` and `CLAUDE.local.md` that is a symlink in the main checkout, run
`ln -s "$(readlink <main>/<item>)" <wt>/<item>`.

## Committing the external repo

At close-out and after program waves, when briefed `external store: <repo toplevel>`:
1. `<external dir>` is the parent project directory of the resolved symlink target in `<repo>`.
2. `git -C <repo> add -A -- <external dir>`.
3. Pathspec commit: `git -C <repo> commit -m "chore(memory): <name>: <what>" -- <external dir>`,
   with the `git-safety` trailer.

Never push or pull in `<repo>`, never stage or touch residue there, and never stage anything in
the project checkout for this commit. `repo-workflow` Sync With Origin does not apply to
`<repo>`.

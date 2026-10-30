# Keeping Memory Outside The Repo

A project's memory lives in `.supervisor/` and `CLAUDE.local.md`. In a repo you cannot commit them to (open source, a shared team repo, a repo you do not own) they sit as local files in one checkout: invisible to git, gone with the clone, and not shared with your linked worktrees or your other machines. `claude-supervisor memory` moves them into a directory outside the repo and leaves two symlinks behind, so the store is the same live store everywhere it is linked, and you can put that directory under version control and sync it yourself.

When you choose a local store, the answer ends with a hint to run `claude-supervisor memory externalize`. The three examples below cover the three cases: moving the store out once, using it from a linked worktree, and using it on another machine. They assume a project checked out at `/home/you/src/proj` and the default external root.

## Example 1: Move The Store Out Of The Repo

Run this once, in the project's main checkout:

```bash
cd /home/you/src/proj
claude-supervisor memory externalize
```

```text
moved: /home/you/src/proj/.supervisor -> /home/you/.local/share/claude-supervisor/memory/proj/.supervisor
linked: /home/you/src/proj/.supervisor -> /home/you/.local/share/claude-supervisor/memory/proj/.supervisor
created: /home/you/.local/share/claude-supervisor/memory/proj/CLAUDE.local.md
linked: /home/you/src/proj/CLAUDE.local.md -> /home/you/.local/share/claude-supervisor/memory/proj/CLAUDE.local.md
excluded: /.supervisor in /home/you/src/proj/.git/info/exclude
excluded: /CLAUDE.local.md in /home/you/src/proj/.git/info/exclude
created README.md: /home/you/.local/share/claude-supervisor/memory/proj/README.md
ignored: .supervisor/working/residue/ in /home/you/.local/share/claude-supervisor/memory/proj/.gitignore
externalized: /home/you/.local/share/claude-supervisor/memory/proj
```

A `moved:` line means the project had that item; a `created:` line means it had none and the tool made an empty one. The project now holds two symlinks, and git ignores them. The memory itself is in `~/.local/share/claude-supervisor/memory/proj/`.

To give the memory its own history, make that directory a repo:

```bash
cd ~/.local/share/claude-supervisor/memory && git init    # one repo for all projects
# or: cd ~/.local/share/claude-supervisor/memory/proj && git init    # one repo per project
```

The project name comes from the origin URL, else the folder name. Pass `--name` to choose another, and `--root` to use another external root:

```bash
claude-supervisor memory externalize --name proj --root ~/memory
```

## Example 2: Use It From A Linked Worktree

Worktrees the pack creates get the two links automatically. For a worktree you made yourself, run `link` inside it:

```bash
git worktree add ../proj-feature
cd ../proj-feature
claude-supervisor memory link
```

```text
linked: /home/you/src/proj-feature/.supervisor -> /home/you/.local/share/claude-supervisor/memory/proj/.supervisor
linked: /home/you/src/proj-feature/CLAUDE.local.md -> /home/you/.local/share/claude-supervisor/memory/proj/CLAUDE.local.md
linked: /home/you/.local/share/claude-supervisor/memory/proj
```

All worktrees share the one external store, so what an agent records in a worktree is there from the main checkout too. The exclude file is shared by the worktrees, so no new lines are needed.

## Example 3: Use It On Another Machine

Clone the memory repo and the project, then link:

```bash
git clone <memory repo> ~/.local/share/claude-supervisor/memory
git clone <project repo> ~/src/proj && cd ~/src/proj
claude-supervisor memory link
```

```text
linked: /home/you/src/proj/.supervisor -> /home/you/.local/share/claude-supervisor/memory/proj/.supervisor
linked: /home/you/src/proj/CLAUDE.local.md -> /home/you/.local/share/claude-supervisor/memory/proj/CLAUDE.local.md
excluded: /.supervisor in /home/you/src/proj/.git/info/exclude
excluded: /CLAUDE.local.md in /home/you/src/proj/.git/info/exclude
linked: /home/you/.local/share/claude-supervisor/memory/proj
```

If you cloned the memory repo somewhere else, or the project's name differs, pass `--root DIR`, `--name N`, or the project's memory directory itself: `claude-supervisor memory link ~/memory/proj`.

## What `externalize` Does

The symlinks are absolute, and Claude Code reads `CLAUDE.local.md` through its link as before. The exclude lines go in `.git/info/exclude`; the project's `.gitignore` is never touched. The `README.md` in `<root>/<name>/` says which project the directory belongs to and how to move it back. The `.gitignore` there keeps test leftovers (the residue ledger, see [workflow-lifecycle.md](workflow-lifecycle.md)) out of the memory history.

The external root is `$CLAUDE_SUPERVISOR_MEMORY_ROOT`, else `${XDG_DATA_HOME:-~/.local/share}/claude-supervisor/memory`; `--root` overrides both. It is data, not config, so it survives `claude-supervisor uninstall`.

`externalize` and `link` are safe to repeat: a second run only repairs what is missing. When either refuses, its message names the repair.

`--global` installs have no launcher; run `./deploy memory --global <verb>` from a checkout. Windows is not supported.

## Daily Flow

Nothing changes. Agents read and write `.supervisor/` as before; the files land in the external directory. Once that directory is a repo, the pack commits memory changes there at close-out and after each wave of a large plan, as `chore(memory): ...` commits. It never pushes or pulls: add a remote and push when you choose.

## Status And Troubleshooting

`claude-supervisor memory status` is a read-only check of the links and exclude lines. It exits 1 when something is off, and each message names its repair.

- **Dangling link:** the external directory moved or is missing (a fresh machine without the clone). Restore it, or remove the link and run `memory link`.
- **Missing exclude line:** rerun `externalize` or `link`; it adds the line.
- **Tracked store:** git tracks `.supervisor` or `CLAUDE.local.md`. Untrack with `git rm -r --cached`, commit, then rerun.
- **Both exist:** the project has a real store and `<root>/<name>` has one too. Either a move was interrupted, or another project with the same default name already uses `<root>/<name>`. Look at `<root>/<name>/README.md`, which names the project it belongs to, before removing anything. For a name clash, keep both and re-run with `--name`.
- **Same-name projects:** two projects whose default names match share `<root>/<name>`. If the second project has a store, `externalize` stops with `both exist`. If it has none, `externalize` stops with a hint to run `memory link`; do not follow it, since that would attach this project to the other one's memory. In both cases re-run with `--name`.

## Moving Back

```bash
rm .supervisor CLAUDE.local.md                      # the two symlinks
mv <root>/<name>/.supervisor <root>/<name>/CLAUDE.local.md .
```

The exclude lines can stay; they keep the restored local store out of git.

## Sharing With A Team

The external directory is an ordinary git repo, so a team can share one memory repo and each member links their checkout to a clone of it. Nothing merges the store for you: agents write to it freely, so agree on who pushes and pull before starting.

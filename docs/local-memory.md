# Keeping Memory Outside The Repo

A project's memory lives in `.supervisor/` and `CLAUDE.local.md`. In a repo you cannot commit them to (open source, a shared team repo, a repo you do not own) they sit as local files in one checkout: invisible to git, gone with the clone, and not shared with your linked worktrees or your other machines. `claude-supervisor memory` moves them into a directory outside the repo and leaves two symlinks behind, so the store is the same live store everywhere it is linked, and you can put that directory under version control and sync it yourself.

## Setup

When the store is created as local, `curator` ends its report with a hint to run `claude-supervisor memory externalize`. That is the entry point; run it from the project's main checkout:

```bash
claude-supervisor memory externalize            # name from the origin URL, else the folder name
claude-supervisor memory externalize --name proj --root ~/memory
claude-supervisor memory status                 # read-only check; exit 1 with a repair hint
```

The external root is `$CLAUDE_SUPERVISOR_MEMORY_ROOT`, else `${XDG_DATA_HOME:-~/.local/share}/claude-supervisor/memory`; `--root` overrides both. It is data, not config, so it survives `claude-supervisor uninstall`. The project's directory inside it is `<root>/<name>`.

`--global` installs have no launcher; run `./deploy memory --global externalize` (and the other verbs the same way) from a checkout. Windows is not supported.

## What The Tool Did

- Moved `.supervisor` and `CLAUDE.local.md` to `<root>/<name>/` (or created them, if the project had none) and put an absolute symlink at each old path. Claude Code reads `CLAUDE.local.md` through its link as before.
- Added `/.supervisor` and `/CLAUDE.local.md` to `.git/info/exclude`, so git ignores the links. The project's `.gitignore` is never touched.
- Wrote a `README.md` into `<root>/<name>/` saying what the directory is and how to restore it (the tool rewrites it on every run; it refuses to run over a `README.md` of yours), and a `.gitignore` there holding `.supervisor/working/residue/`, so test leftovers never enter the memory history.

The command is safe to repeat: it checks everything before writing, and a second run only repairs what is missing.

## Making The Directory A Repo

Run `git init` at the root (one repo for all projects) or in `<root>/<name>` (one per project). Either works, and the residue ignore applies before or after. From then on `git-ops` commits the project's directory at close-out and after program waves, with `chore(memory): <name>: <what>`. It never pushes or pulls: add a remote and push when you choose.

## Daily Flow

Nothing changes. Agents read and write `.supervisor/` as before; the files land in the external directory. Commit history of the memory builds up there, separate from the project's.

## A Fresh Machine

```bash
git clone <memory repo> ~/.local/share/claude-supervisor/memory   # or any directory, then use --root
git clone <project repo> && cd <project>
claude-supervisor memory link                                     # --root DIR, --name N, or an explicit DIR
```

`link` attaches the project to the existing external directory: the two symlinks and the exclude lines. It refuses when `.supervisor` is a real directory in the project (use `externalize`) or when nothing exists at the external path.

## Linked Worktrees

All worktrees share the one external store, so what an agent records in a worktree is there from the main checkout too. When `executor` cuts a worktree it recreates the two symlinks. For a worktree you made yourself, run `claude-supervisor memory link` inside it. The exclude file is shared by the worktrees, so no new lines are needed.

## Troubleshooting

Each message names its repair.

- **Dangling link:** the external directory moved or is missing (a fresh machine without the clone). Restore it, or remove the link and run `memory link`.
- **Missing exclude line:** rerun `externalize` or `link`; it adds the line.
- **Tracked store:** git tracks `.supervisor` or `CLAUDE.local.md`. Untrack with `git rm -r --cached`, commit, then rerun.
- **Both exist:** the project has a real store and the external directory has one too, for example after an interrupted move. Decide which to keep and remove the other.
- **Same-name projects:** two projects whose default names match share `<root>/<name>`, so the second `externalize` stops at the existing store. Give one of them `--name`, and do not follow the `link` hint for it.

## Moving Back

```bash
rm .supervisor CLAUDE.local.md                      # the two symlinks
mv <root>/<name>/.supervisor <root>/<name>/CLAUDE.local.md .
```

The exclude lines can stay; they keep the restored local store out of git.

## Sharing With A Team

The external directory is an ordinary git repo, so a team can share one memory repo and each member links their checkout to a clone of it. Nothing merges the store for you: agents write to it freely, so agree on who pushes and pull before starting.

---
name: repo-workflow
description: Default rules for versioning, branches, worktrees, checks and landing changes in a repo. Preloaded by executor, planner and git-ops; the brief and the repo's CLAUDE.md override it. Use before committing, bumping a version, branching, cutting a worktree, merging, or choosing which checks to run.
user-invocable: false
---

# Repo Workflow

The brief and the repo's `CLAUDE.md` (plain prose; there is no config file) override these defaults.

## Projects only

Decide first whether the directory is a project, per `project-memory` (Projects and one-offs); a
git repo whose toplevel is neither `$HOME` nor above it always is one. Outside a project nothing is
persisted:
- Only the read-only defaults apply: work in the current checkout (no worktree, no merge), create,
  bump or tag no version, never force-push the default branch, run the checks the repo names.
- Ask no versioning question. Never create or write `CLAUDE.md`, `VERSION` or a changelog for this
  skill; a new `CLAUDE.md` would itself turn the directory into a project.

## Versioning

- Never create, bump or tag a version, or write a changelog entry, unless the brief or `CLAUDE.md`
  says to.
- A repo that already versions its own way (a version field in `pyproject.toml` or `package.json`,
  release tags, a maintained `CHANGELOG`) keeps its scheme. Do not change or bump it unless told to,
  and say in the report when a change may need a bump.
- A repo whose `CLAUDE.md` says it uses the `repo-workflow` `X.y` scheme follows the next section.
- A project with no versioning and no `CLAUDE.md` line about it: the agent that commits a change to
  the default branch commits it unversioned and ends its report with this one question, verbatim:
  ```
  versioning: none declared. Adopt the repo-workflow X.y scheme?
  Yes: add "Versioning: uses the repo-workflow X.y scheme." to CLAUDE.md and create VERSION
  holding 1.0.
  No: add "Versioning: none; do not ask."
  ```
  Never ask once `CLAUDE.md` records an answer.
- Whoever is briefed with the answer writes that one line to `CLAUDE.md` at the project root and,
  on yes, creates `VERSION`.

## The X.y Scheme

- `VERSION` holds `X.y`. y rises by one once per change set that lands on the default branch. X
  rises, and y resets to 0, when a major change lands; the user, `CLAUDE.md` or the plan says what
  is major.
- The agent that lands a change set on the default branch bumps `VERSION` with it, before running
  the checks: the lead in its squash commit, the editing agent for a direct Mode 1 commit, and
  `git-ops` for a Mode 2 commit. `curator` and `clerk` never commit; `clerk` edits `VERSION` only
  when its brief says so. Never every worker.
- Work on other branches leaves `VERSION` alone; the change is bumped when it lands on the default
  branch.
- `git-ops` stages a modified `VERSION` with the commit. On the default branch, when
  `git diff HEAD --stat -- VERSION` is empty, it raises y itself before committing.

## Branches And Worktrees

- In a git project, each `executor` change set works in its own `git worktree` at
  `<toplevel>/.claude/worktrees/<slug>`, on a new branch cut from the default branch. Name the
  branch like the repo's existing branches, else `<type>/<slug>`. Workers share the lead's
  worktree, and only the lead changes git state in it. Quick-tier work (`clerk`, `git-ops`),
  conflict resolution, environment repair and repos with submodules stay in the current checkout.
- Before cutting a worktree, run `git worktree list`: resume in the one for your own slug, and
  report the other linked worktrees as "other worktrees". If
  `git check-ignore -q .claude/worktrees/<slug>` fails, append the line `/.claude/worktrees/` to
  `$(git rev-parse --git-path info/exclude)`. Never edit `.gitignore` for this.
- Clean up other worktrees only when the user asks, never with `--force`: commit uncommitted edits
  on their branch as a `wip:` commit, `git worktree remove` the worktree, delete its branch
  (`git branch -d`) only if `git log <default>..<branch>` is empty, then `git worktree prune`.
- When the brief or the user explicitly says to work in place or in a named checkout or worktree,
  work and commit there, and merge only when asked.
- Untracked setup the checks need: copy small ignored files (`.env`, local config) into the
  worktree. Never link a venv or `node_modules`; build them in the worktree with the project's tool
  (`uv sync`, `npm ci`), and ask when it is unclear what is needed. Check that the tests import the
  worktree's code (for Python, `python -c 'import <pkg>; print(<pkg>.__file__)'`).
- Read and tick a plan at the path the brief gives, not at its copy in the worktree.
- Force-push and rebase of pushed commits stay gated by `git-safety`. A standing permission in the
  repo's `CLAUDE.md` (for example `--force-with-lease` on feature branches after a rebase) counts as
  the explicit user request for the branches it covers. It never covers the default branch, which is
  force-pushed only when the user names it in the brief.
- Store changes: every commit in a project checkout, on any branch, also stages that checkout's
  pending `.supervisor/` changes, except while resolving a conflict (`git-safety` conflict
  resolution stages only resolved files). The report lists the store paths it committed.

## Landing A Work Branch

When the task is done and its checks pass, the lead lands the branch it cut, locally. Nothing else
merges into the default branch unless asked; a merge the user asks for of any branch, including
one the user made (a user-made worktree), follows steps 2-5.
1. Commit the change set on the branch, including the worktree's store changes (`git-safety`
   Commits).
2. In the worktree, `git rebase <default>`, then rerun the checks. On a conflict, follow
   `git-safety` (Conflicts).
3. Find the checkout that has the default branch checked out (`git worktree list`). If there is
   none, stop: leave the branch ready and report why. If it has staged changes outside
   `.supervisor/` or an operation in progress, or git fails on a `.lock` file, wait a minute and
   retry from step 2, at most three times, then stop the same way. If
   `git merge-base --is-ancestor <default> <branch>` fails, go back to step 2.
4. There, `git merge --squash <branch>`; if git refuses because it would overwrite uncommitted
   changes only under `.supervisor/`, commit those first with `git add .supervisor` and
   `git commit -m "chore(memory): <what>" -- .supervisor` (in an `X.y` repo, raise `VERSION` and
   add it to the pathspec, as this lands on the default branch), then go back to step 2; if it
   names other paths, stop: leave the branch ready and report. Otherwise `git add .supervisor`, so
   this checkout's pending store changes join the squash commit. Bump `VERSION` if the repo uses
   the `X.y` scheme, run the checks, and commit once
   `git diff --cached --quiet <branch> -- . ':!VERSION'` (add `':!.supervisor'` when the commit
   takes this checkout's pending store changes) confirms the staged tree is the branch. Other
   unrelated uncommitted changes stay out of the commit. If the checks or that test fail, do not
   commit; report, leave the squash staged, and stop (keep the worktree and branch). Never move
   the default branch with `update-ref` or `branch -f`.
5. `git worktree remove <path>` without `--force` (if it refuses, keep it and report). Once
   `git diff --quiet HEAD <branch> -- . ':!VERSION'` (add `':!.supervisor'` when the commit took
   this checkout's pending store changes) confirms the commit holds the branch, delete it
   with `git branch -D`; this default is the user's request for that deletion.
6. Never push. Report the worktree, the branch, and the squash commit or why it did not merge.

## Checks

- Run the checks the brief, `CLAUDE.md` or README names (tests, lint, type checks, a build), else
  the cheapest meaningful one (a compile, `--help`, a sample run).

# Research: Worktrees For Agentic Parallel Work

Scope: where and how the pack should place, share, provision and clean up git worktrees when leads
work in parallel, measured against the v4.1 baseline in `pack/skills/repo-workflow/SKILL.md`
("Branches And Worktrees", lines 54-70; "Landing A Work Branch", lines 72-89) and
`pack/agents/executor.md`. Out of scope: implementing any pack change. Gathered 2026-10-22 on
Linux, git 2.34.1, Claude Code 2.1.308, pack v4.1. Labels: **[V]** verified (official docs, source,
repo path:line, or a local experiment in a scratch repo), **[I]** inference, **[C]** community or
secondary source. Experiments ran on git 2.34.1. Features from git 2.48+ come from the docs only.
Web pages were read through a summarizing fetch, so check the quotes against the page before
reusing them.

## Recommendation

1. **Location.** Put the worktree inside the repo, at `<toplevel>/.claude/worktrees/<slug>`, on
   branch `<type>/<slug>`. If `git check-ignore -q .claude/worktrees/<slug>` fails, append
   `/.claude/worktrees/` to `$(git rev-parse --git-path info/exclude)`. That is one untracked line
   in the shared `.git`, and it covers every worktree. Do not edit `.gitignore` for this.
   Reasons:
   - The location keeps worktrees out of `~/projects`, so nothing lands outside the project.
   - It is the directory Claude Code itself uses.
   - Ripgrep, git, pytest and ruff skip it once it is excluded.
   - It sits on the same filesystem as the repo, so uv and pnpm hardlinks keep working.

   Prefer this over XDG or `$TMPDIR` locations, which are outside the project, hard to find, and in
   the tmpfs case lost on reboot.
2. **Parallelism.** Keep one worktree per change set (per lead). Workers share the lead's worktree
   with disjoint files, as now, and only the lead changes git state in it. Parallel leads each get
   their own worktree. The shared `.git` tolerates concurrent use: contention fails fast on a lock
   file, and the only corruption risk is from concurrent gc, which git's docs rate low. Landings
   serialize on the default branch's checkout, as follows:
   - A lead that finds that checkout busy waits briefly and retries from the rebase step, instead
     of giving up at once.
   - Before committing the squash, the lead checks that the staged tree equals its branch. Today's
     busy check narrows the race but does not close it: two squashes can stack under one bump.
   - `VERSION` needs nothing else, because the bump happens in the squash commit and reads the
     version that is current at landing time.
3. **Environment.**
   - Copy small gitignored files (`.env`, local config).
   - Do not symlink a venv or `node_modules`. Build a per-worktree environment with the project's
     own tool (`uv sync`, `npm ci`/`pnpm install`), which is cheap on the same filesystem.
   - If an environment must be shared, run the checks with the worktree's code first on the path.
     Then verify the import location: a shared venv with an editable install silently tests the
     main checkout.
   - Repos with submodules work in place.
4. **Lifecycle.**
   - Before cutting a worktree, the lead runs `git worktree list`. It resumes in a worktree that
     matches its own slug and lists the other pack worktrees in its report as "other worktrees".
     The supervisor, which knows which leads are in flight, calls those with no running lead
     leftovers.
   - Leftovers are cleaned only when the user asks, and never with `--force`:
     1. Commit uncommitted edits on their branch as a `wip:` commit.
     2. `git worktree remove`.
     3. Delete the branch only if it holds nothing beyond the default branch.
     4. `git worktree prune`.
   - Skip `git worktree lock`.

## Evidence

### Q1 Location

Claude Code's built-in worktrees:
- **[V]** `--worktree`, `EnterWorktree` and subagent `isolation: "worktree"` all create
  `<repo>/.claude/worktrees/<name>/` on branch `worktree-<name>`, cut by default from `origin/HEAD`
  (setting `worktree.baseRef`: `"fresh"` or `"head"`)
  (https://code.claude.com/docs/en/worktrees).
- **[V]** The docs recommend adding `.claude/worktrees/` to `.gitignore`.
- **[V]** The 2.1.308 binary also writes `**/.claude/worktrees/` into `.git/info/exclude` under a
  `# claude-code-runtime` block (binary strings; it is not known which version added this).
- **[V]** Cleanup: a clean, unnamed worktree is removed on exit. A dirty one prompts to keep or
  remove. Subagent and background worktrees with changes stay until a sweep after
  `cleanupPeriodDays`. The sweep skips worktrees with changes, unpushed commits, or no Claude marker,
  so it never touches worktrees the pack creates with plain `git worktree add`.
- **[V]** Claude Code holds `git worktree lock` while an agent runs, and its sweep releases locks
  left by dead processes.
- **[V]** `EnterWorktree` paths under `.claude/worktrees/` need no approval prompt.
- **[V]** `.worktreeinclude` copies matching gitignored files.

Other tools ([V] unless marked; sources in the worker table, summarized):
- Codex app: `$CODEX_HOME/worktrees`, keeps the 15 most recent, snapshots before deleting
  (https://learn.chatgpt.com/docs/environments/git-worktrees).
- Claude Squad: `<config>/worktrees/` (smtg-ai/claude-squad `session/git/worktree.go`).
- gwq: `~/worktrees/<host>/<owner>/<repo>/<branch>` (https://github.com/d-kuro/gwq).
- worktrunk: a sibling `../<repo>.<branch>` by default, with a local `wt merge` that squashes and
  cleans up (https://worktrunk.dev/config/).
- Cursor: `.cursor/worktrees.json` setup scripts; its docs advise against symlinking dependencies
  (https://cursor.com/docs/configuration/worktrees, search snippet).
- Conductor uses setup and archive scripts with `CONDUCTOR_ROOT_PATH` and `CONDUCTOR_PORT`
  (https://www.conductor.build/docs/reference/scripts); Simon Willison uses fresh checkouts in
  `/tmp` (https://simonwillison.net/2025/Oct/5/parallel-coding-agents/).
- No surveyed tool serializes concurrent landings.
- Pattern **[I]**: agent tools hide worktrees in-repo or in a tool-owned home directory, and
  human-facing CLIs use siblings.

Comparison:

| Location | Clutter | Discoverable | Cleanup | Tools recurse | Same fs |
|---|---|---|---|---|---|
| Sibling `<repo>-wt-<slug>` (today) | Clutters `~/projects` | Easy | Manual, invisible from the repo | No | Usually |
| In-repo `.claude/worktrees/` | None outside the repo | `git worktree list`, `ls .claude/worktrees` | Visible, and dies with the repo | Some (see below) | Yes |
| XDG `~/.cache/...`, `~/.local/share/...` | Hidden global state | Poor | Orphans accumulate unseen | No | Usually |
| `$TMPDIR` | None | Poor | Lost on reboot, then `prune` is needed | No | Often not (tmpfs) |

Tool effects of the in-repo location, from scratch-repo experiments **[V]**:
- Without an exclude, `git status` shows `?? .worktrees/`, and `git add -A` stages the worktree as
  an embedded-repo gitlink. With `/.worktrees/` in `.git/info/exclude`, status is clean.
  `info/exclude` lives in the common dir and so applies to all worktrees
  (gitrepository-layout: `info` is shared).
- `git clean -fdx` prints `Skipping repository .worktrees/x`. `git clean -ffdx` would delete it
  (git-clean docs).
- `rg` skips dot-dirs by default. `ruff` does not skip dot-dirs, but honours both `.gitignore` and
  `info/exclude`.
- pytest's default `norecursedirs` includes `.*` (`_pytest/main.py:229-231`), so a dot-dir worktree
  is never collected. A non-dot `worktrees/` dir caused `import file mismatch` and aborted
  collection, and gitignore did not help. So the directory name must start with a dot.
- `find` recurses into it.
- **[I]** (from memory, not fetched): mypy, tsc, jest, vitest, eslint flat config and VS Code's
  file watcher do not skip `.claude/` by default. VS Code also lists nested repos in Source
  Control. These tools only matter when a project runs them unscoped.
- **[C]** Claude Code's grep and rg wrappers skip `.claude/worktrees/`, and its `find` does not
  (claudeissues #88402, search snippet only).
- **[I]** CLAUDE.md discovery changes. Claude Code loads a subdirectory's `CLAUDE.md` and
  `.claude/rules` files once it reads a file there (https://code.claude.com/docs/en/memory). The
  docs exempt only subagents in their own `isolation` worktree. A lead that reads files under
  `<repo>/.claude/worktrees/<slug>/` from the main checkout may therefore load the branch's copy
  of `CLAUDE.md` a second time. A sibling worktree is not a subdirectory, so it avoids this.
  Untested.
- **[V]** A worktree on another filesystem works: git links by path, not by hardlinks. uv falls back
  to a full copy across filesystems (`Failed to hardlink files; falling back to full copy`).

Why not adopt `isolation: "worktree"` for leads:
- **[V]** It cuts from `origin/HEAD` unless the user sets `worktree.baseRef: "head"`. For a pack
  that lands locally and never pushes, `origin/HEAD` lags the local default branch.
- **[V]** Subagent Bash commands that resolve to the main checkout fail, which conflicts with the
  local squash in the main checkout. **[I]** That makes landing awkward.
- Reusing the location gets the benefits without the coupling.

### Q2 Parallelism

**[V]** Which state is per-worktree and which is shared:
- `HEAD`, `index`, `index.lock`, `ORIG_HEAD`, rebase state, `FETCH_HEAD` and `refs/worktree`,
  `refs/bisect` and `refs/rewritten` are per-worktree.
- `refs/`, `packed-refs`, objects, config, hooks and `info/` are shared
  (https://git-scm.com/docs/git-worktree, REFS; https://git-scm.com/docs/gitrepository-layout).

**[V]** Concurrency in experiments:
- Concurrent commits in three worktrees (40 each) gave no errors and a clean `fsck`.
- A ref or `packed-refs` collision fails with `Unable to create '...lock': File exists`.
- `git gc` docs: concurrent gc carries "some risk of corruption (which seems to be low in
  practice)". `git maintenance run` takes a lock and skips colliding tasks.

**[V]** Hazards:
- `git worktree add` refuses a branch that is checked out elsewhere, unless `--force` is given.
- `git -C <other-wt> update-ref refs/heads/main HEAD` succeeded and left the main checkout's index
  stale. So land only by merging in the checkout that has the default branch, as step 3 already
  says, and never move that branch by `update-ref` or `branch -f` from elsewhere.

**[I]** Per-worker worktrees would multiply environment setup and add N merges, while lead-loop
already guarantees disjoint files. `executor-worker.md:24` already forbids workers to change git
state, so concurrent index locks cannot arise inside one worktree.

Landing and `VERSION`:
- **[V]** (critic scratch experiment) Two consecutive `git merge --squash` runs of different
  branches both returned 0 and left both change sets staged.
- **[I]** So step 3's "staged changes, stop" check narrows the race but does not close it. If lead
  B checks before lead A stages, B stacks onto A's squash, and one commit with one bump carries
  both. A check before the commit that the staged tree equals the branch
  (`git diff --cached --quiet <branch> -- . ':!VERSION'`, the index-side form of step 5's test) closes it in practice. On a mismatch both leads stop, and
  the staged squash needs a manual reset.
- **[I]** Branches never touch `VERSION`, so rebases never conflict on it, and sequential landings
  give y+1, then y+2. Today a lead that loses the race gives up instead of retrying.

### Q3 Environment

- **[V]** The editable-install trap: with a venv whose editable `.pth` points at `main/src`,
  `import demo` from inside a worktree loaded the main checkout's code. A linked venv therefore
  defeats the existing rule "check that the tests import the worktree's code" (`SKILL.md:63-64`).
- **[V]** `pyvenv.cfg` and the scripts hold absolute paths, so a venv is not relocatable.
- **[V]** Gitignored copies (`.env`, a `.venv/` directory) let `git worktree remove` succeed. A
  symlinked `.venv` does not match the `.venv/` pattern, so it is untracked and blocks `remove`;
  `remove --force` deletes only the link.
- **[I]** Other environments and services:
  - uv: `uv sync` per worktree is cheap through the hardlinked global cache.
  - conda: a named env is shared, so the editable trap recurs.
  - pnpm: hardlinks from its store make a per-worktree install cheap.
  - Docker Compose: names the project after the directory basename, so worktrees with distinct
    slugs do not collide.
  - Ports and local databases: clash only when checks start services.
- **[V]** git-worktree BUGS: "the support for submodules is incomplete. It is NOT recommended to
  make multiple checkouts of a superproject."
- **[V]** Hooks come from the common dir and are shared, so they run in worktrees.
- **[V]** Claude Code skips LFS and filter drivers when it creates worktrees.
- **[I]** LFS smudge runs normally for a plain `git worktree add`; this is untested.

### Q4 Lifecycle

- **[V]** `git worktree list --porcelain` reports `locked <reason>` and `prunable`.
- **[V]** `remove` refuses a dirty tree, and a locked one needs `-f -f`.
- **[V]** `prune` only drops the admin entries of worktrees whose directory is gone, and gc does this
  after `gc.worktreePruneExpire` (3 months). An in-repo worktree whose directory exists is never
  pruned.
- **[V]** Moving the repo breaks linked worktrees until `git worktree repair <paths>` runs.
  `worktree.useRelativePaths` (git 2.48+) avoids this, but older gits cannot read such a
  repository.
- **[I]** On locks: a lock left by a crashed lead looks the same as one held by a live lead, and
  Claude Code needs a PID-aware sweeper to make its locks useful. Without that machinery a lock
  adds a `-f -f` hazard and no information.
- **[I]** Detecting orphans: the pack's worktrees are on `<type>/<slug>` branches, and Claude Code's
  are on `worktree-*` or `agent-*`. Only the supervisor knows which leads it has running in its own
  session, so only it can tell a leftover from a parallel lead's live worktree. A stopped or crashed lead that is
  re-briefed with the same slug finds its own worktree and resumes.
- **[I]** Uncommitted edits: a `wip:` commit on the worktree's own branch keeps them in history
  and makes `remove` succeed without `--force`. A stash is repo-wide, easy to lose, and not tied to
  the branch.
- **[V]** Baseline gaps (`SKILL.md:72-89`, worker grep of `pack/`):
  - No step finds or cleans leftovers, so a stopped task leaves no pointer.
  - No `git worktree lock`, `git worktree prune`, `isolation:` or `EnterWorktree` appears in
    `pack/`.
  - `project-backup` already excludes `.claude/worktrees/` (`pack/skills/project-backup/SKILL.md:33`).

## Proposed Changes (ranked)

Caps from `tests/test_pack_lint.py:21-24`, used/cap: `repo-workflow` 906/1300 words, 94/300
lines; executor 448/700; supervisor 999/1000; git-ops 349/350.

1. `repo-workflow` "Branches And Worktrees": replace the sibling placement with
   `<toplevel>/.claude/worktrees/<slug>` plus the `check-ignore` / `info/exclude` line. About +35
   words.
2. `repo-workflow` setup bullet: apply Recommendation 3 (copy ignored files, per-worktree
   environments, the import-location check `python -c 'import pkg; print(pkg.__file__)'`,
   submodule repos in place). Step 5 shrinks to "remove setup links". About +45 words.
3. `repo-workflow`: a new bullet "Other worktrees": before cutting a worktree, run
   `git worktree list`, resume in your own slug, and report the others; clean up only on request,
   per Recommendation 4. About +50 words.
4. `repo-workflow` "Landing": in step 3, on a busy default checkout or a lock error, wait and retry
   from step 2 up to three times before leaving the branch ready. In step 4, before the commit,
   stop unless `git diff --cached --quiet <branch> -- . ':!VERSION'` passes. Never move the
   default branch by `update-ref`/`branch -f`. About +45 words.
5. `executor.md` Final Output: add "and other worktrees found". About +5 words. The supervisor
   relays that line as it relays the rest of the report; whether a listed worktree is live or a
   leftover is visible to it from its own dispatches in this session, so no supervisor text is needed.
6. `docs/architecture.md:31` still reads correctly, so no change is needed. Supervisor and git-ops:
   no change, because the caps are full and the lead-side rules make one unnecessary.

Total is about +175 words in `repo-workflow`, within its headroom of 394.

## Risks And Gaps

- `git clean -ffdx`, `cp -r` and `rsync` of the repo reach in-repo worktrees.
- A lead reading worktree files may load the branch's `CLAUDE.md` and rules twice **[I]**.
- Existing sibling worktrees need one manual move or removal.

## Open Questions For The User

1. Location: `.claude/worktrees/` (shared with Claude Code, recommended), `.worktrees/`, or keep
   siblings?
2. Leftovers: report only and clean on request (recommended), or let the supervisor have clean
   leftovers removed without asking (no running lead, no edits, nothing beyond the default
   branch)? A lead in another, parallel session would look like a leftover.
3. Busy landing: wait and retry (recommended), or keep "leave ready and report" and let the
   supervisor re-dispatch?
4. Submodule repos: work in place (recommended), or a worktree plus
   `git submodule update --init`?

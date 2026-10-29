# Plan: externalize a project's memory store

## Goal

Let a user of the deployed pack keep a project's `.supervisor/` and `CLAUDE.local.md` outside a
repo they cannot commit them to: a `claude-supervisor memory` subcommand moves (or creates) them
in an external per-project directory, replaces the project-side paths with symlinks, and excludes
those through `.git/info/exclude`; the pack treats the externalized store as a local store that
linked worktrees share and that `git-ops` commits when the external directory is a git repo.
Also fix two latent bugs: store READMEs created before the exclude rule still say "add
`.supervisor/` to `.gitignore`" and are never rewritten; the curator `(local)` procedure both
stages and says not to stage.

Non-goals: Windows, automatic push or pull of the external repo, a snapshot or rsync mode,
`.claude/settings.local.json`, team-sharing support beyond a paragraph, changing the
tracked/local question in `supervisor.md`.

Expected change size: about 850 lines. `deploy` +300, tests +300, docs +190 (new
`docs/local-memory.md` about 120), pack text about 60 lines changed, README +10. Next minor.

## Approach

One `memory` subcommand with three verbs (`externalize`, `link`, `status`) in `deploy`, reached
through the launcher like `status`. The external layout mirrors the project (`<root>/<name>/
.supervisor/`, `<root>/<name>/CLAUDE.local.md`), so externalizing is a `move` plus two symlinks
and restoring is two symlinks; nothing else is persisted, the symlink itself records the location.
The pack learns about externalization through the mechanism, not the tool: `.supervisor` being a
symlink. The existing local-store rules (`git check-ignore -q` succeeds; plain `mv`, no staging)
already hold for it; the deltas are that linked worktrees share it and that `git-ops` commits
inside the external repo at close-out and after program waves.

Rejected: a snapshot/rsync backup (the user's `sync-memory.sh` prior art: two copies that
drift, no residue filter, collisions overwrite under `--delete`); a state file naming the root
(the symlink already does; a fresh machine passes `--root` or the directory once); a pack-side
script instead of a `deploy` subcommand (the user fixed the entry point); making curator or
supervisor offer externalization in the tracked/local question (not strictly needed, and the
supervisor file is at its word cap; see Scope Notes).

## Decisions

- D1 Default root: `${CLAUDE_SUPERVISOR_MEMORY_ROOT}`, else
  `${XDG_DATA_HOME:-~/.local/share}/claude-supervisor/memory`; `--root DIR` overrides. Data,
  not config: it must survive `claude-supervisor uninstall` (which deletes the profile dir) and
  is per project, not per profile or tag.
- D2 Per-project directory: `--name`, else the `origin` URL's basename with a trailing `/` and
  `.git` stripped, else the toplevel's basename. A name containing `/` or equal to `.`/`..` is
  refused. Two projects with one basename collide on the default name: `externalize` refuses
  an external item that already exists (D3), and the doc tells the user to pick `--name`. The
  external `README.md` states `project:` and `origin:` as prose for the human reader; nothing
  parses it.
- D3 Verbs. `externalize`: move-or-create, main checkout only; `link`: attach to an existing
  external directory (fresh machine, linked worktree, explicit `DIR`); `status`: read-only check,
  exit 1 with a repair hint. Both writing verbs preflight both items before any write and refuse
  as a whole when either item conflicts; both are idempotent and repair the exclude lines, the
  external `.gitignore` and both READMEs on every run. Per item, the project path is absent,
  real, a link to the expected external path, or another link (dangling included); the external
  item is present or absent. `externalize`: real + absent -> move; absent + absent -> create;
  expected link -> no-op; real + present -> refuse ("both exist"); absent + present -> refuse
  ("run `memory link`"); other link -> refuse (names the target). `link`: absent + present ->
  symlink; absent + absent -> refuse for `.supervisor`, create an empty file for
  `CLAUDE.local.md`; expected link -> no-op; real or other link -> refuse (hint `externalize`,
  or remove the link). A fourth verb to move the store back is out of scope; the doc shows the
  two `mv` commands.
- D4 The project-side `.supervisor` is moved, never copied: `shutil.move` (works across
  filesystems), then an absolute symlink. A `.supervisor` or `CLAUDE.local.md` that git tracks
  (`git ls-files --error-unmatch`) is refused with the `git rm -r --cached` hint; untracking is a
  repo change the user makes. The resolved external directory must lie outside every checkout
  of the repo: not equal to or under the main toplevel or any path listed by
  `git worktree list --porcelain`, else exit 2 before any write; this also keeps D6's
  `.gitignore` out of the project repo.
- D5 Exclude lines are `/.supervisor` and `/CLAUDE.local.md` without trailing slash: verified
  that `/.supervisor/` does not match a symlink (`git check-ignore` rc 1) while `/.supervisor`
  does. The curator `(local)` line changes to the slash-less form too, so a later `externalize`
  needs no new line; existing `/.supervisor/` lines stay. `info/exclude` is per repo and shared
  by linked worktrees (`git rev-parse --git-path info/exclude` in a worktree prints the main
  checkout's file, verified).
- D6 Residue stays out of external git history through `<external>/.gitignore` holding the
  line `.supervisor/working/residue/`, written unconditionally (created, or the line appended),
  so it holds before or after a `git init` at `<root>` or at `<root>/<name>`. No repo detection.
  The project repo's `.gitignore` is never touched (`project-memory`).
- D7 A new store (no `.supervisor` yet) is created by the tool from the installed template
  `<target>/skills/project-memory/templates/store-readme.md`, with `CLAUDE.local.md` as an
  empty file so both symlinks resolve; the pack text says `curator` or the tool creates stores.
  The template missing means the pack is not installed at `<target>`: error, exit 2.
- D8 README fix (bug a), both routes: the tool replaces `<external>/.supervisor/README.md` with
  the installed template when they differ, and `curator` does the same on every run for any
  store (staged for a tracked store). SKILL.md's "never edit that README" becomes "replaced from
  the template, never edited"; the repo's own `.supervisor/README.md` (old wording) is left for
  curator's next run, not edited here.
- D9 Curator `(local)` contradiction (bug b): staging is for `(tracked)` only; `(local)` is never
  staged (preamble). Reworded, not re-decided.
- D10 Linked worktrees share the externalized store: nothing merges a local store, so
  per-worktree stores would be lost or merged by hand. The executor recreates the two symlinks
  when it cuts a worktree (`repo-workflow`, Branches And Worktrees); `memory link` in a worktree
  does the same by hand. `git worktree remove` accepts the ignored symlinks (verified).
- D11 `git-ops` commits the external repo at close-out and after program waves (user
  decision). The rule lives once, in `project-memory` Committing the store: a git-excluded store
  is reported as `not staged: store untracked`, or as `external store: <repo toplevel>` when
  `.supervisor` is a symlink whose target lies in another git repo. `curator` (close-out) and
  `fixer` (post-wave plan edits; it preloads `project-memory`) both end with that line;
  supervisor briefs `git-ops` on it as it does for staged paths (word-neutral edit at
  `pack/agents/supervisor.md:95-96`, the only supervisor change). `git-ops` runs
  `git -C <repo> add -A -- <external dir>` and a pathspec commit `chore(memory): <name>:
  <what>`, never pushes or pulls there. Leads' off-default-branch pathspec commits stay skipped
  for a local store.
- D12 Residue check: `git check-ignore` on a path beyond a symlink is fatal (rc 128, verified), so
  the `residue` precheck becomes "unless `.supervisor` is a symlink or the check succeeds",
  otherwise every run would append a duplicate exclude line.
- D13 Pack word budget. Lint caps leave `supervisor.md` 1 word, `residue` 1, `repo-workflow` 2,
  `git-ops` 9, `fixer` 2, `project-memory/SKILL.md` 22 (`tests/test_pack_lint.py:22-25`). The `git-ops`
  procedure and the worktree symlink step go in a new uncapped reference,
  `pack/skills/repo-workflow/references/external-store.md`; SKILL.md edits are word-neutral by
  trimming nearby prose, checked by the lint.
- D14 Naming inside `project-memory`: the skill describes the mechanism ("`.supervisor` is a
  symlink into a directory outside the repo"), per
  `.supervisor/memory/decisions/2026-10-22-project-memory-rules-are-generic.md`; the command
  name appears in the store README template, `docs/`, and README.
- D15 `--global` installs have no launcher (`docs/deploy.md:93`); they run `./deploy memory …`
  from a checkout, as for `doctor`. Documented, not solved.
- D16 Non-git directories and `os.name != "posix"` are refused with a one-line message.
- D17 The external `README.md` is tool-owned: its first line is the marker
  `<!-- claude-supervisor memory: rewritten on every run -->`. The tool rewrites it when absent
  or when the first line is the marker, and refuses (exit 2, before any write) when some other
  `README.md` is there; `link` additionally requires `<external>/.supervisor/` to exist. Apart
  from this file, `<external>/.gitignore` (D6, append-only) and the template-owned
  `<external>/.supervisor/README.md` (D8), nothing in the external directory is ever
  overwritten or deleted.
- D18 (owner, 2026-10-29) Discoverability: the curator `(local)` procedure ends its report with
  one hint line that supervisor relays verbatim, for example `hint: to keep this store outside
  the checkout or across machines, run claude-supervisor memory externalize` (exact wording the
  executor's; one line; no `supervisor.md` edit). `docs/local-memory.md` opens its setup flow
  with that hint as the entry point.
- D19 (owner, 2026-10-29) `--global` installs keep the documented limitation (D15). This change
  set adds a roadmap item to `.supervisor/roadmap.md` (Items, after the last numbered item),
  worded as an open decision: "deprecate `--global` installs, or ship the deploy tool with them
  so `memory`/`doctor` work without a checkout"; the owner leans toward deprecation. Ancillary
  path, no version effect.
- D20 (owner, 2026-10-29) Order and version: this change set lands first on `main` as the next
  minor. The parallel workflow-lifecycle change set is a major on a feature branch with its own
  `CHANGELOG.md` entry and rebases on top of this one; this change set touches `supervisor.md`
  only at lines 95-96 and never `CHANGELOG.md`.

## Outline

`deploy` (new block after `doctor_cmd`, `deploy:1921`; follow `migrate` at 1791 for the handler
shape and `doctor` at 2168-2171 for parser wiring):

```
LAUNCHER_COMMANDS = ("update", "uninstall", "list", "status", "critic", "memory")   # deploy:61
MEMORY_ITEMS = ((".supervisor", True), ("CLAUDE.local.md", False))                  # (name, is_dir)
RESIDUE_IGNORE = ".supervisor/working/residue/"
def memory_root(args) -> Path                 # D1
def memory_project(cwd) -> Tuple[Path, Optional[Path]]   # (main toplevel, worktree toplevel or None)
def memory_name(toplevel, override) -> str    # D2
def memory_externalize_cmd(args) -> int; memory_link_cmd(args) -> int; memory_status_cmd(args) -> int
def memory_attach(toplevel, external, template) -> None   # shared tail: symlinks, excludes,
                                                           # external README, .gitignore, store README
```

- Launcher: add `memory` to the `case` at `deploy:132` (`update|uninstall|list|status|memory`)
  and to `LAUNCHER_HELP`; `main()` at 2186 already fixes target for launcher calls.
- Parser: `add_parser("memory", ...)` with its own `add_subparsers(dest="verb", required=True)`
  for the three verbs; `common(sp, source=False)` on `memory` (the template needs `--target`/
  `--global`; the launcher fixes them). `link` takes optional positional `dir`; `externalize` and
  `link` take `--root`, `--name`.
- Git calls follow `deploy:448-497` (`subprocess.run(["git", "-C", ...], capture_output=True,
  text=True, timeout=10)`). Worktree: resolved `--git-common-dir` != resolved `--git-dir` means
  linked; main toplevel is the common dir's parent, refuse when its basename is not `.git`.
- Exclude file: `git rev-parse --git-path info/exclude` from the main toplevel; create `info/`
  if absent; append missing lines only (no duplicates).
- External `README.md` (D17): marker line, what the directory is, `project: <toplevel>`,
  `origin: <url or none>`, the restore commands.
- Output: one `print` line per action (`moved`, `linked`, `created`, `excluded`, `ignored`,
  `refreshed README`) and a final `externalized: <external>`; errors raise `DeployError` (exit 2).
- Invariants: preflight, then write (D3); never delete or overwrite user content (D17); never
  write inside the project except the two symlinks and `info/exclude`; never run
  `git add`/`commit` anywhere.

`tests/test_deploy_memory.py` (new; reuse `load_deploy()` `tests/test_deploy.py:84-90`, `run()`
56-70 and the `pack`/`target` fixtures 27-52; build repos with the `git()` helper pattern at
1290-1298; set `HOME` so D1 resolves under `tmp_path`).

`pack/skills/project-memory/SKILL.md:36-38, 47-52, 99-101`: D7, D8, D10, D14 wording; `:47-49`
becomes "no agent stages or commits it; linked worktrees get it only when it is externalized
(`.supervisor` a symlink into a directory outside the repo, shared by all worktrees), else
not at all".
`pack/skills/project-memory/references/curator-procedures.md:12-15, 112-121`: D8 refresh step
(preamble), D11 report line, D9 rewording, D5 slash-less line.
`pack/skills/project-memory/templates/store-readme.md:3-5`: one sentence naming
`claude-supervisor memory externalize` for a store kept outside the repo.
`pack/skills/residue/SKILL.md:26-28`: D12.
`pack/skills/repo-workflow/SKILL.md:64-70, 85-86`: one pointer each to the new reference
(worktree cut; store changes), word-neutral.
`pack/skills/repo-workflow/references/external-store.md` (new, about 25 lines): detection
(`[ -L .supervisor ]`, `git -C "$(readlink -f .supervisor)" rev-parse --show-toplevel` differing
from the project toplevel), worktree symlink recreation (`ln -s "$(readlink <main>/.supervisor)"
<wt>/.supervisor`, same for `CLAUDE.local.md`), the `git-ops` commit procedure (D11), and what
it never does (push, pull, touch residue, stage in the project).
`pack/agents/git-ops.md:18-26`: one "Do" line, at most 9 words net, pointing at the reference.
`pack/agents/supervisor.md:95-96`: D11 trigger, word-neutral.
`pack/agents/fixer.md:35`: the parenthetical "(unstaged for a git-excluded store, per
`project-memory`)" becomes "(for a git-excluded store, `project-memory`'s report line)",
word-neutral; `pack/agents/curator.md` unchanged.
`docs/local-memory.md` (new): why; setup; what the tool did; making the external dir a repo
(`git init` at the root or per project, agents commit, you push, residue ignored); daily flow;
fresh machine (`git clone <memory repo> ~/.local/share/claude-supervisor/memory` or `--root`,
clone the project, `memory link`); worktrees; troubleshooting limited to what `status`
reports (dangling link, missing exclude line, tracked store) plus "both exist" and same-name
projects (`--name`); `--global` and Windows as one line each in setup; moving back; one
team-sharing paragraph.
`docs/deploy.md:70-94` launcher list gains `memory …`; new `## Memory` section before
`## Doctor Checks` (250) in the `## Migrate` shape (`deploy.md:289-302`), linking
`docs/local-memory.md`.
`README.md:171` gains a sentence and link; docs list `:213-215` and layout line `:278` gain
`docs/local-memory.md`. `docs/architecture.md:102` gains one sentence on externalized stores
(no inventory change: `git-ops` and `curator` roles are unchanged).

## Slices

1. Externalize and status, end to end.
   Delivers: `claude-supervisor memory externalize` and `memory status` on a main checkout,
   launcher routing, deploy doc section.
   Units: (a) `deploy`; (b) `tests/test_deploy_memory.py`; (c) `docs/deploy.md`.
   Tests:
   - externalize_moves_existing_store: real `.supervisor` + `CLAUDE.local.md` -> both are
     symlinks to `<root>/<name>/…`, content preserved, `git check-ignore -q` rc 0 for both,
     `git status --porcelain` empty.
   - externalize_creates_new_store: no store -> external `.supervisor/README.md` equals the
     template byte for byte, empty `CLAUDE.local.md`, both symlinks.
   - externalize_name_from_origin: `git@h:org/proj.git` -> `proj`; no origin -> toplevel
     basename; `--name x` -> `x`; `--name a/b` -> exit 2.
   - externalize_refuses_tracked_store: committed `.supervisor/x.md` -> exit 2, message names
     `git rm -r --cached`.
   - externalize_refuses_existing_external: external `.supervisor` present, project's absent ->
     exit 2, hint `memory link`; nothing written.
   - externalize_refuses_other_link: project `.supervisor` links elsewhere -> exit 2, names the
     target; nothing written.
   - externalize_preflight_atomic: `.supervisor` movable but `CLAUDE.local.md` conflicts -> exit
     2 and `.supervisor` still a real directory.
   - externalize_refuses_inside_project: `--root <toplevel>/mem` -> exit 2 before any write;
     the same with `--root <linked worktree>/mem`.
   - externalize_refuses_foreign_readme: `<external>/README.md` without the marker -> exit 2;
     file unchanged.
   - externalize_in_linked_worktree: run in a worktree -> exit 2, names the main checkout.
   - externalize_idempotent: second run -> exit 0, exclude file has each line once.
   - externalize_refreshes_old_readme: old `.gitignore` wording -> template text after run.
   - externalize_gitignore_before_git: externalize with no repo, then `git init` at root and a
     file under `working/residue/` -> absent from `git -C root status --porcelain`; second run
     keeps one line.
   - externalize_requires_pack: target without the template -> exit 2.
   - externalize_outside_git: plain dir -> exit 2.
   - status_ok / status_dangling / status_missing_exclude: exit 0; exit 1 and `dangling`; exit 1
     and `missing /.supervisor`.
   - launcher_routes_memory: launcher text `case` includes `memory`; `LAUNCHER_COMMANDS` too;
     existing `test_launcher_*` (`tests/test_deploy.py:567-600`) still pass.
   Checkpoint: `python3 -m pytest -q tests/test_deploy_memory.py tests/test_deploy.py`.

2. Link: fresh machine, explicit directory, linked worktree.
   Delivers: `memory link` (default root, explicit `DIR`, linked worktree).
   Units: (a) `deploy`; (b) tests; (c) `docs/deploy.md` link lines.
   Tests:
   - link_fresh_machine: external exists, project has no store -> symlinks and exclude lines.
   - link_explicit_dir: `memory link DIR` ignores root and name.
   - link_refuses_real_store: project has a real `.supervisor` -> exit 2, hint `externalize`.
   - link_missing_external: nothing at `<root>/<name>` -> exit 2, names the path.
   - link_in_worktree: main externalized, `git worktree add`, `link` in the worktree -> same
     targets, `git -C wt status --porcelain` empty, `git worktree remove` succeeds.
   - link_repairs_partial: `.supervisor` already the expected link, `CLAUDE.local.md` absent ->
     exit 0, second link created, exclude lines complete.
   - link_refuses_other_link: `.supervisor` a dangling link -> exit 2, hint to remove it.
   Checkpoint: `python3 -m pytest -q tests/test_deploy_memory.py`.

3. Pack behaviour: shared worktrees, git-ops commit, bug fixes, residue check.
   Delivers: agents handle an externalized store without new tooling.
   Units: (a) `pack/skills/project-memory/` (SKILL.md, procedures, template); (b)
   `pack/skills/repo-workflow/` (SKILL.md pointers, new reference) and `pack/skills/residue/
   SKILL.md`; (c) `pack/agents/git-ops.md`, `pack/agents/supervisor.md:95-96`,
   `pack/agents/fixer.md:35`; (d) `docs/architecture.md:102`.
   Tests (lint):
   - pack_lint passes: `python3 -m pytest -q tests/test_pack_lint.py` (word caps, line length,
     skill refs).
   - procedures_local_consistent: `grep -n "git add .supervisor" curator-procedures.md` shows the
     staging only under `(tracked)`.
   - local_hint_present: `grep -c "memory externalize" curator-procedures.md` is 1, in the
     `(local)` paragraph (D18).
   - residue_precheck: `grep -n "symlink" pack/skills/residue/SKILL.md` finds the D12 condition.
   Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py` and a read-through of the
   reference file against D10-D11.

4. User docs, version, end-to-end smoke.
   Delivers: `docs/local-memory.md`, README text, `VERSION` next minor.
   Units: (a) `docs/local-memory.md` (setup flow opens with the D18 hint); (b) `README.md`;
   (c) `.supervisor/roadmap.md` item (D19); (d) `VERSION` (one agent, before the checks).
   Tests:
   - version_bumped: `python3 -m pytest -q tests/test_version.py` passes with the working tree
     diff.
   Checkpoint: every `docs/*.md` path named in README.md and docs/*.md exists (grep); then
   `python3 -m pytest -q`, `/usr/bin/python3 -m py_compile deploy` and a
   scratch smoke run (`./deploy install --target <tmp>`, a scratch repo, `externalize`,
   `status`, `git worktree add`, `link` in the worktree, `status`).

## Verification

After slice 4: `python3 -m pytest -q` green; `/usr/bin/python3 -m py_compile deploy` and
`./deploy memory --help` succeed; in a scratch repo under the session scratchpad with
`XDG_DATA_HOME` pointed into it: `externalize` moves and links, `git status --porcelain` is
empty, `<external>/.gitignore` holds the residue line, `git init` on the root then
`git -C root status` hides a residue file, a linked worktree plus `link` shows the same
targets, `status` exits 0; `grep -rn "gitignore" pack/skills/project-memory/` shows only "never"
wording. Residue: the scratch dirs are recorded and torn down per `residue`.

## Risks

- Python 3.9: no 3.9 interpreter here (`/usr/bin/python3` is 3.10); avoid `match`, `X | Y`
  annotations and parenthesized context managers; `Path.readlink` is 3.9+. Checked by
  `py_compile` and review.
- Two worktrees write one store concurrently (plans ticked, residue ledgers): same exposure as a
  shared tracked store on one branch; accepted.
- `shutil.move` across filesystems copies then deletes: a crash mid-way leaves a partial external
  copy and the original intact; `externalize` then refuses (both exist) and the message tells the
  user which to remove. No test covers the crash.
- Pack word caps: trims in dense skills can lose meaning; the critic reads the trimmed sentences.
- Another lead edits `pack/agents/supervisor.md` in parallel: this change set touches only lines
  95-96, word-neutral; the later commit rebases over the earlier.
- The external root shared by many projects as one repo: `git-ops` stages only
  `<root>/<name>`, so other projects' dirty files stay out of its commits; untested with two
  projects dirty at once.
- A moved project (toplevel renamed) keeps working (absolute symlinks); the external README's
  `project:` line goes stale until the next `externalize`/`link` run.
- Same-basename projects: `externalize` in the second project refuses ("run `memory link`"), and
  a user who follows that hint attaches the first project's memory. The refusal text and the doc
  name `--name` for this case; no automatic detection.

## Scope Notes

In: the subcommand with three verbs, launcher wiring, tests, pack wording for externalized
stores, both bug fixes, `docs/local-memory.md`, README and deploy doc text, architecture
paragraph, next-minor bump. Out: Windows, auto push/pull, snapshot or rsync mode,
`settings.local.json`, a move-back verb, changing the supervisor's tracked/local question or any
`supervisor.md` line other than 95-96, editing this repo's own `.supervisor/README.md`,
`CHANGELOG.md` (minor bump). User decisions the executor must not reopen: live externalized
store, not a snapshot; `deploy` subcommand via the launcher; `.git/info/exclude` never
`.gitignore` (`project-memory`); residue out of external history; `git-ops` commits, user pushes
(`.supervisor/memory/decisions/2026-10-24-git-ops-not-curator-or-clerk-commits.md`); minor bump
(`.supervisor/memory/decisions/2026-10-27-version-bumps-only-for-product-changes.md`).

Coordination (D20): lands first on `main` as the next minor; the workflow-lifecycle major
rebases on top. `supervisor.md` edits stay at lines 95-96; `CHANGELOG.md` is not touched; the
roadmap item (D19) rides in this change set as an ancillary path.

## Assumptions

- `git` 2.34+ semantics for `check-ignore`, `worktree`, `rev-parse --git-path` hold on the user's
  machine; checked by the slice 1-2 tests on the executor's git.
- Claude Code keeps reading `CLAUDE.local.md` through a symlink; checked by the smoke run.
- `tests/test_pack_lint.py` caps reference files only by line length, not words; checked by
  running the lint after slice 3.
- The launcher regenerates on `install`/`update`, so existing installs gain `memory` on their
  next update; checked by `test_launcher_*`.

## Open Questions

None. The owner approved the plan on 2026-10-29 with the amendments recorded as D18-D20;
discoverability now goes through the curator hint (D18) instead of a `supervisor.md` edit.

## Log

- 2026-10-28 planner: done, plan written and passed critic round 3; deferred: none
- 2026-10-29 decision: curator `(local)` report ends with a one-line hint naming `claude-supervisor memory externalize`, relayed verbatim by supervisor; no `supervisor.md` edit; source: user
- 2026-10-29 decision: `--global` installs keep the checkout-only limitation; roadmap item "deprecate `--global` installs, or ship the deploy tool with them" added as an open decision, owner leans to deprecation; source: user
- 2026-10-29 decision: this change set lands first on `main` as the next minor; the workflow-lifecycle major rebases on top; `supervisor.md` only at lines 95-96, no `CHANGELOG.md` edit; source: user
- 2026-10-29 executor: done, landed 05985ef on main as v8.2 (all 17 Todo items); review: codex round 1 eight findings fixed, round 2 PASS, scope-critic five cuts applied; deferred: none
- 2026-10-29 decision: curator's D18 hint goes just before the mandatory `recorded N` last line, since curator.md is unchanged; `status` takes no --root/--name and reads the .supervisor symlink; `link` requires the installed template

## Todo

- [x] S1 `deploy`: `LAUNCHER_COMMANDS`, launcher `case` and help, `memory` parser with verbs,
      root/name/project resolution, `externalize`, `status`, `memory_attach` tail
- [x] S1 tests: the 18 externalize/status/launcher cases
- [x] S1 `docs/deploy.md`: launcher list and `## Memory` section
- [x] S2 `deploy`: `link` (default, explicit dir, worktree)
- [x] S2 tests: the 7 link cases
- [x] S2 `docs/deploy.md`: link lines
- [x] S3 `project-memory/SKILL.md`: D7, D8, D10, D11 report rule, D14 wording within 22 words
      net
- [x] S3 `curator-procedures.md`: preamble README refresh, `external store:` line (rule in
      SKILL.md); `(local)` rewording and one-line externalize hint (D18); slash-less exclude line
- [x] S3 `store-readme.md`: one sentence naming the tool
- [x] S3 `residue/SKILL.md`: symlink precheck, word-neutral
- [x] S3 `repo-workflow/references/external-store.md` new; SKILL.md pointers word-neutral
- [x] S3 `git-ops.md` one line; `supervisor.md:95-96` and `fixer.md:35` word-neutral
- [x] S3 `docs/architecture.md:102` sentence; lint green
- [x] S4 `docs/local-memory.md` (setup opens with the D18 hint)
- [x] S4 `.supervisor/roadmap.md`: `--global` open-decision item (D19)
- [x] S4 `README.md:171`, docs list, layout line
- [x] S4 `VERSION` next minor; `python3 -m pytest -q`; `/usr/bin/python3 -m py_compile deploy`;
      scratch smoke run and residue teardown

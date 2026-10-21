# Plan: memory Stage 4, move the working set out of `docs/`

Roadmap: `ROADMAP.md` item 1 "Persistence and long-term memory (2.x)", subsection "Stage 4: Move
the working set out of `docs/`" (item 5 before the 2026-10-21 reorder). Stage 5 is out of scope.
Planned against `main` at 798477d; `main` keeps moving, so the branch is cut from its head at
Setup. Lands as the Stage 4 squash merge, the next minor on `main` (D9).

## Goal

Agent working state (research, plans and their `## Log`) lives under `.supervisor/working/` and is
archived to `.supervisor/archive/working/`, so `docs/` holds only human documentation. A reusable
curator procedure migrates an existing project's `docs/` working set; this repo is migrated with
it. Done when (roadmap): a full program writes nothing to `docs/` except documents the user asked
for; this repo's `docs/` holds only human documentation; the procedure runs in another project;
the suite passes.

## Approach

1. **Path switch, no new mechanism.** Default paths become
   `.supervisor/working/research/research-<topic>.md` and
   `.supervisor/working/plans/plan-<topic>.md`; the curator's archive step and idle-plan sweep
   retarget to the `archive/working/` mirror. File names keep their `research-`/`plan-` prefixes,
   so a migrated file keeps its name and a moved `source:` resolves by name.
   Rejected: `plans/<topic>.md` without prefix (renames every migrated file, breaks lookup by name).
2. **Migration is `curator migrate docs/`**, a second form of the existing `migrate <path>` brief
   (today only for a legacy `docs/writing-rules.md`). Live files move to `working/`; each spent
   file in `docs/archive/` is distilled into `decision`/`fact` entries still in force, then moved
   to `archive/working/<area>/`. It reuses the brief form and `follow-up:` lines; the five-entry cap
   does not apply to any `migrate` run (OQ4). Rejected: a migration command in `deploy` (deploy
   never touches projects, and distillation needs judgment); new programs only (D3 decided a
   one-time migration).
3. **Moved sources are resolved, not rewritten.** Entries are never edited and `history.md` is
   append-only, so the 24 `source:` lines and `history.md:3` that cite
   `docs/archive/plan-memory-v2.md` stay; one sentence in `project-memory` says how to find a
   moved source. Rejected: rewriting `source:` lines (breaks supersede-never-edit); superseding 24
   entries (churn with no new claim).
4. **Legacy detection lives in the curator.** Its every-run sweep proposes `curator migrate docs/`
   while `docs/` still holds `plan-*`/`research-*` files, as `writer` proposes the writing-rules
   migration. Rejected: detection in `planner` or `supervisor` (38 and 1 words of headroom).
5. **`supervisor.md` and `executor.md` stay untouched.** The roadmap lists them for path updates,
   but neither names a working-set path (grep), and the supervisor is at 999 of 1000 words.
6. **Roadmap.** The roadmap moves to `.supervisor/roadmap.md` (OQ1 (b), answered 2026-10-21). Its
   reference format (items name `goal` entries and cite `decision` entries, never prose) is I5 and
   gates P2 only.

### How this plan migrates

- It is written at `docs/plan-memory-stage4.md` (the v2.0 convention the stable agents follow)
  and committed on `main` as its own change set with its own `VERSION` bump, as v2.0's plan was
  (7f2c8f2).
- Once the branch exists, the plan is edited only on the branch, in the worktree: `Status`,
  `## Todo` and `## Log`. Main's copy stays frozen until the squash, so no commit on `main` needs a
  `VERSION` bump for plan bookkeeping and rebases never conflict on it.
- P3 moves it as a live plan to `.supervisor/working/plans/plan-memory-stage4.md` (same name).
  From P3's report on, every brief and `clerk` Log append names that path.
- P4's close-out archives it to `.supervisor/archive/working/plans/plan-memory-stage4.md`, and its
  `history.md` line cites that path. The squash merge carries the moves to `main`.

## Files to create or modify

| Package | File | Lines | Change |
|---|---|---|---|
| P1 | `pack/agents/researcher.md` | 16 | default path to `.supervisor/working/research/research-<topic>.md` |
| P1 | `pack/agents/planner.md` | 16, 44, 64 | default path; fresh-research glob and "nothing under `.supervisor/archive/` is fresh"; Artifacts template |
| P1 | `pack/agents/writer.md` | 33 | `.supervisor/working/research/research-*.md` |
| P1 | `pack/agents/curator.md` | 3, 17-19, 46 | migrate covers a legacy `docs/` working set (at most 40 words added) |
| P1 | `pack/skills/project-memory/SKILL.md` | 21, 32, 46-56, 86-87 | drop "until Stage 4" wording; add the source-resolution sentence (I4); procedure list |
| P1 | `pack/skills/project-memory/references/curator-procedures.md` | 3-8, 32, 40, 69-80 | legacy proposal (I3); archive step and sweep glob (I1); `migrate docs/` (I2) |
| P1 | `pack/skills/project-memory/templates/store-readme.md` | 8 | `research/` by `researcher`, `plans/` by `planner` |
| P1 | `README.md` | 85, 96, 151, 157, 158, 222-223 | new paths; tree drops `docs/archive/` |
| P1 | `REVIEW.md` | 28 | `.supervisor/archive/` replaces `docs/archive/` |
| P1 | `docs/architecture.md` | 29, 30, 40, 60, 64, 80 (working/ part) | new paths; curator row names `migrate docs/` |
| P2 | `ROADMAP.md`, `git mv` to `.supervisor/roadmap.md` (OQ1 (b)) | `docs/` pointers (14, 32, 43, 87, 88, and Science artefacts' Pointers); maintenance rule 19; item 1 Decisions (46-82); Science artefacts; Roadmap intake's last sentence | paths, references, item format (I5) |
| P2 | `pack/skills/project-memory/SKILL.md` | 15-16, 102-106 | roadmap row (`.supervisor/roadmap.md`); the Horizons section (same roadmap path, plans and research in `working/`) |
| P2 | `pack/skills/project-memory/references/curator-procedures.md` | 24-31 | roadmap step uses the item's `Decisions:` paths (I5) |
| P2 | `README.md` / `docs/architecture.md` | 225 / 80 (roadmap clause) | roadmap path `.supervisor/roadmap.md` |
| P3 | `docs/research-memory.md`, `docs/plan-memory-stage4.md` | - | `git mv` to `.supervisor/working/research/`, `.../plans/` |
| P3 | `docs/archive/*` (8 plans, 1 research) | - | distilled, then `git mv` to `.supervisor/archive/working/{plans,research}/` |
| P3 | `.supervisor/memory/{decisions,facts}/` | new | entries still in force |
| P4 | `.supervisor/history.md`, `.supervisor/roadmap.md` Stage 4 subsection | append / remove | curator close-out |
| P4 | `VERSION` | - | raised by one in the squash commit on `main` only |

Line numbers are from the 2026-10-21 inventory and drift as `main` moves (the roadmap gained an
item during planning); units re-grep before editing. Roadmap items are named by title.

## Interfaces and data changes

**I1. Paths.** Only the default paths change; a caller-supplied path still wins.

```
.supervisor/working/research/research-<topic>[-<id>].md   researcher (default)
.supervisor/working/plans/plan-<topic>[-<id>].md          planner (default; child plans add -<id>)
.supervisor/archive/working/research/                      curator archive step, same file name
.supervisor/archive/working/plans/                         curator archive step, same file name
```

The idle-plan sweep lists `.supervisor/working/plans/plan-*.md`.

**I2. `curator migrate docs/`.** A writing-rules path keeps today's procedure. For `docs/`:

1. Live: `git mv` each `docs/plan-*.md` and `docs/research-*.md` to `working/plans/` or
   `working/research/` under the same name. No entries.
2. Spent: for each `docs/archive/plan-*.md` and `docs/archive/research-*.md`, write one `decision`
   or `fact` entry per decision or fact still in force (`## Decisions`, `## Scope Notes`, decided
   Open Questions, research conclusions), checking neighbours as in close-out step 3, with
   `source: .supervisor/archive/working/<area>/<name>#<section>`; then `git mv` the file there. A
   file moves only after its entries exist, so what remains in `docs/archive/` is the follow-up
   (`follow-up: curator migrate docs/`). Lessons are proposed only (D7).
3. Every other file in `docs/` is human documentation and stays. An emptied `docs/archive/` goes.
4. Report: moved paths, entries written, and files outside `.supervisor/` that still name a moved
   file (grep by name) for the user to update; last line `recorded N`.

In a one-off it reports the `not stored:` line (`curator.md:28-30`); in a project it creates the
store on its first write (`SKILL.md:29`). Plain `mv` when `.supervisor/` is gitignored
(`SKILL.md:54-56`).

**I3. Legacy proposal.** On every run, beside the idle-plan sweep: if `docs/` holds `plan-*.md` or
`research-*.md`, here or under `docs/archive/`, the report adds `follow-up: curator migrate docs/`.

**I4. Moved sources** (one sentence in `SKILL.md` near the entry rules): a `source:` path that no
longer exists names a moved file; find the same name under `.supervisor/archive/`, else run
`git log --all -- <path>`.

**I5. Roadmap item format** (P2). Items reference other items by
title, since numbers shift as items land.

```
### <n>. <title>
- **Goals:** <goal entry paths>          only when the item serves one (none exist today; OQ3)
- **Decisions:** <decision entry paths>  replaces "Decisions already made" prose
- **Depends on:** <item titles>          only when it has any
(Goal, Scope, Left to planner, Done when, Pointers and the Priority/Effort line unchanged)
```

The curator's roadmap step copies the item's `Decisions:` paths into the `history.md` line and
still records any remaining prose bullet as an entry first (legacy roadmaps).

**Data.** P3 adds about 30 entries (inventory estimate; superseded items skipped). Setup records
one decision entry for item 1's bullet "the owner confirms the open decisions at planning;
implement each stage with the minimum rule text", which has none. The OQ1 and OQ4 answers are
recorded (2026-10-21); the three-horizons entry stands (OQ1 (b)). P4's
close-out re-verifies entries whose `affects:` changed (`docs/`, `pack/skills/project-memory/`)
per D6.

## Risks and compatibility

- **Bootstrapping.** The program runs on the stable agents, which default to `docs/`. Every package
  is `execute` only; if a research or child plan becomes necessary, its brief names a
  `.supervisor/working/` path.
- **Wrong or stale entries from old plans.** The P3 brief carries the superseded-item list below;
  the owner reviews entry summaries in `git diff` before the commit.
- **Word caps.** `curator` has 40 words of headroom, `planner` 38; path rewrites are one token
  each. `supervisor` (999/1000) and `critic` (600/600) are not edited. Lines stay at most 100 chars.
- **Rebase conflicts.** Main may gain roadmap items during the program; rebase after every package.
- **Other projects.** Unmigrated projects keep working: briefs name plan paths, close-out archives
  any named plan to the new mirror, and I3 proposes the migration. A project that gitignores
  `.supervisor/` takes its plans out of version control on migration; that follows its D1 choice.
- **Dev install.** Dropped by the owner on 2026-10-21 (`supervisor-dev` uninstalled): steps that
  name the dev tag (Setup's install, V7, dev-tag sessions) use the suite and simulated runs instead.

## Acceptance criteria and validation

- V1, another project: in a fixture repo without a store (Orchestration), `curator migrate docs/`
  under the dev tag: the store is created, live files in `.supervisor/working/`, spent files in
  `.supervisor/archive/working/` under the same names, an entry for the in-force fixture decision
  and none for the superseded one, `docs/guide.md` untouched, inbound references reported.
- V2, full program: in the fixture, a dev-tag research, plan and execute run of a toy change;
  `git -C <fixture> status --porcelain -- docs` is empty, and research and plan exist under
  `.supervisor/working/`; `curator close-out` moves both to `.supervisor/archive/working/`.
- V3, this repo: `git ls-files docs` lists only `docs/architecture.md` and `docs/deploy.md`.
- V4, sweep: in the fixture, a working plan with a Log line older than 30 days is proposed for
  archiving, and a leftover `docs/plan-x.md` draws `follow-up: curator migrate docs/`.
- V5, paths: `grep -rnE 'docs/(plan|research|archive)' pack README.md REVIEW.md
  docs/architecture.md` returns only the legacy-path lines of I2 and I3 in
  `curator-procedures.md`; on `.supervisor/roadmap.md`, after P2, it returns only lines inside
  the Stage 4 subsection, which P4's close-out removes.
- V6, suite: `python3 -m pytest -q` has no failures on the branch and on `main` after the squash.
- V7, version: `claude-supervisor-dev --version` shows
  `<VERSION at the merge-base>+memory-stage4.<ahead>.g<sha>` matching
  `git -C ../claude-supervisor-dev rev-parse --short HEAD` before each V run.

## Scope Notes

- In: I1-I5; the path updates listed above; this repo's migration; the roadmap at
  `.supervisor/roadmap.md`.
- Out: Stage 5 (hooks, D10); the other roadmap items (the Roadmap intake item's README section stays
  its own item; P2 only syncs its last sentence to `.supervisor/roadmap.md`); `deploy` changes
  (derived versions and the downgrade guard are used as they are; `deploy` never touches
  `docs/` or `.supervisor/`); edits to
  `supervisor.md`, `executor.md`, `critic.md`; new goal entries (OQ3); the stale `.gitignore:9`
  `docs/research/` line; Finder or Obsidian visibility checks.
- Decisions that bind (entries in `.supervisor/memory/decisions/`, prefix `2026-10-21-`):
  - D1 `project-memory-lives-in-supervisor-in.md`; D2 `store-layout-is-memory-per-kind-working.md`;
    D3 `research-and-plans-move-out-of-docs-at.md`; D4 `a-sonnet-curator-curates-memory-clerk.md`;
    D5 `the-post-wave-clerk-records-mid-program.md`; D6 `expiry-flags-an-entry-when-its-affects.md`;
    D7 `memory-holds-decisions-then-facts.md`; D8 `writing-rules-are-conventions-per-draft.md`;
    D9 `stages-1-3-of-memory-land-together-as-v2.md` (a minor bump, not a major `X.0`);
    D10 `no-retrieval-hooks-in-v2-0-add-one-only.md`;
    D11 `one-file-per-entry-kinds-decision-fact.md`;
    D12 superseded by D13 `one-off-directories-persist-nothing-and.md`.
  - Also: `memory-work-was-developed-on-a-feature.md` (dev flow);
    `folders-hold-fixed-properties-labels.md` (no status field, supersede never edit);
    `history-md-holds-one-line-per-landed.md`; `idle-plans-30-days-without-log-activity.md`;
    `in-v2-0-working-holds-only-writing.md` (this stage completes it);
    `no-supervisor-word-cap-raise-the-archive.md`; `the-curator-owns-goal-entries-the-clerk.md`;
    `three-horizons-are-goals-roadmap-and.md` (binds; OQ1 (b) affirms it);
    `roadmap-lives-in-supervisor-roadmap-md.md` (OQ1) and
    `migration-is-exempt-from-the-entry-cap.md` (OQ4), both answered 2026-10-21;
    `installs-are-standalone-of-the-deploy.md` (no step relies on an install reading its checkout).
- Creep to resist: a roadmap template file or planner rule about roadmap items; rewriting
  `source:` lines; a migration script; a new agent or hook; a cap raise.

## Assumptions

- A1. No agent or skill text names working-set paths beyond the inventory. Check: V5 grep.
- A2. The stable install accepts explicit `.supervisor/working/` paths in briefs. Check:
  `planner.md:16` ("Use a caller-supplied path").
- A3. `docs/research-memory.md` is live research (ROADMAP.md:87 cites it for Stages 4-5), so it
  moves to `working/research/` and P4's close-out leaves it there. Check: that pointer.
- A4. Branch `memory-stage4`, worktree `../claude-supervisor-dev` and tag `supervisor-dev` are
  free (true on 2026-10-21 apart from the leftover directory in Setup). Check:
  `git worktree list`, `git branch --list memory-stage4`, `./deploy list`.

## Work Packages

### P1: Working-set paths and the migrate procedure
- Goal: agents and the curator use `.supervisor/working/` and its archive mirror, and
  `curator migrate docs/` exists; done when V5 (pack and docs) and V6 pass and V1 passes on the
  dev tag.
- Owns: `pack/agents/{researcher,planner,writer,curator}.md`; `pack/skills/project-memory/`
  (except `SKILL.md:15-16, 102-106` and `curator-procedures.md:24-31`); `README.md` (except 225);
  `REVIEW.md`; `docs/architecture.md` (except the roadmap clause of 80).
- Deps: none
- Stages: execute
- Status: done
- Artifacts: commit on `memory-stage4`

### P2: Roadmap location and references
- Goal: the roadmap sits at `.supervisor/roadmap.md`, in the I5 format, with pointers to
  migrated paths; done when item 1 and Science artefacts carry no "Decisions already made"
  prose, V5 is clean for the roadmap and V6 passes.
- Owns: `ROADMAP.md` (`git mv` to `.supervisor/roadmap.md`); `SKILL.md:15-16, 102-106`;
  `curator-procedures.md:24-31`; `README.md:225`; the roadmap clause of `docs/architecture.md:80`.
- Deps: P1 (shared files, disjoint lines); P3 (same memory folder and git index; moves the files
  P2 points at)
- Stages: execute
- Status: done
- Artifacts: commit on `memory-stage4`

### P3: Migrate this repo
- Goal: run `curator migrate docs/` on this repo under the dev tag; done when V3 passes and the
  owner has accepted the new entries.
- Owns: `docs/research-memory.md`, `docs/plan-memory-stage4.md` (moves only), `docs/archive/**`,
  `.supervisor/memory/**`, `.supervisor/working/{research,plans}/`, `.supervisor/archive/working/`
- Deps: P1
- Stages: execute
- Status: done
- Artifacts: commit on `memory-stage4`; plan path afterwards
  `.supervisor/working/plans/plan-memory-stage4.md`

### P4: Validate, close out and land
- Goal: V1-V7 pass, the plan is closed out and the branch lands as 2.x; done when `main` carries
  the squash commit with `VERSION` raised by one, `./deploy status` is clean and the dev tag, the
  worktree and the branch are gone.
- Owns: `VERSION` (on `main`), `.supervisor/history.md` and the Stage 4 subsection of
  `.supervisor/roadmap.md` (curator), the fixture directory outside the repo.
- Deps: P1, P2, P3
- Stages: execute
- Status: execute
- Artifacts: squash commit on `main`; `.supervisor/archive/working/plans/plan-memory-stage4.md`

## Orchestration

**Setup (supervisor, after approval).**
1. `clerk` records item 1's bullet without an entry (Data); the OQ1 and OQ4 entries exist
   (written 2026-10-21). `executor`
   raises `VERSION` by one and runs the suite; `git-ops` commits the plan and entries on `main`.
2. `git -C <checkout> worktree add ../claude-supervisor-dev \
   -b memory-stage4`
3. `<dev-worktree>/deploy install --tag supervisor-dev`. An
   unregistered `~/.config/claude-supervisor-dev` (only `projects/` and `skills/`) is left from
   v2.0; check how `install` treats it first, and ask the owner before removing it.

As in v2.0 (`docs/archive/plan-memory-v2.md:766-775`): the stable `claude-supervisor` session
drives the program, `claude-supervisor-dev` sessions run the V checks, P3 and the P4 close-out,
and the branch is pushed to origin; rebases on `main` need a force-push (`--force-with-lease`)
of `memory-stage4`, gated per git-safety. After Setup the stable session runs from
`<dev-worktree>`, so Log appends and entries land on the branch; P4
step 3 is the only later work on `main`. Each package brief has `executor` commit on the branch
itself, with no `VERSION` change.

**Waves.** Wave 1: P1. Wave 2: P3. Wave 3: P2 (OQ1 and OQ3 answered). Wave 4: P4. The plan of
record is the branch copy in the worktree.

**P1 units** (one `executor` wave, files disjoint):

| Unit | Owns | Validation by the worker |
|---|---|---|
| U1 | `researcher.md`, `planner.md`, `writer.md` | `grep -nE 'docs/(plan\|research\|archive)'` on the three files is empty; lint |
| U2 | `curator.md`, `references/curator-procedures.md` (not 24-31) | I2, I3 text present; curator under 400 words |
| U3 | `SKILL.md` (not 15-16, 102-106), `templates/store-readme.md` | I4 sentence present; SKILL.md under 1300 words, 300 lines |
| U4 | `README.md` (not 225), `REVIEW.md`, `docs/architecture.md` (not the 80 roadmap clause) | V5 for these files; the curator row matches U2 |

Glue: run V6 and V5, `critic` and `scope-critic` with these Scope Notes, commit on the branch
(no `VERSION`), `./deploy install --tag supervisor-dev` from the worktree, V7, then V1 in a dev-tag
session in the fixture.

**Fixture** (outside the repo, e.g. `$TMPDIR/s4-fixture`): `git init`; `docs/guide.md` (human);
`docs/plan-live.md` and `docs/research-live.md`; `docs/archive/plan-old.md` with a `## Decisions`
section holding one decision in force and one marked superseded; `docs/archive/research-old.md`
with one conclusion; one commit. V4 adds a working plan whose last Log line is dated 40 days back.

**P2.** One `executor` unit. Maps from the inventory: D1-D13 and the two unnumbered bullets to
their entry files; Science artefacts' "Depends on item 1" becomes `Depends on:` by title.

**P3.** A dev-tag session in the worktree dispatches `curator migrate docs/` with this brief: no
entry cap (`migrate` is exempt, OQ4); skip the superseded items (install-lifecycle "out: `list`";
sandboxed-install "`--fable` flag stays"; versioning `1.x` scheme, "no update subcommand", "no
`--version` flag"; opus-default and fable-fallback mechanics; memory-v2 D12); keep
`docs/research-memory.md` and this plan live. The owner reviews `git diff --stat` and the new
`summary:` lines; `git-ops` commits on the branch. P2 or the executor fixes the inbound references
the report lists in editable files (the roadmap is P2's).

**P4.** In order:
1. V1-V7 as one batch in dev-tag sessions; the suite on the branch.
2. Dev-tag `curator close-out .supervisor/working/plans/plan-memory-stage4.md`: archive this plan
   (not `research-memory.md`, which Stage 5 still cites); remove the Stage 4 subsection of
   `.supervisor/roadmap.md`; append the `history.md` line, whose version is `main`'s `VERSION` plus
   one; re-verify flagged entries. The
   owner checks `git diff`; `git-ops` commits on the branch.
3. `executor`: `git rebase main` on the branch, suite, then on `main`
   `git merge --squash memory-stage4`, `VERSION` raised by one, suite, commit, `./deploy install`,
   `./deploy status`.
4. With user confirmation: `git-ops` pushes; `claude-supervisor-dev uninstall`;
   `git worktree remove ../claude-supervisor-dev`; `git branch -D memory-stage4`.

## Open Questions

- **OQ1. Where does the roadmap live after Stage 4?** **Resolved 2026-10-21: (b).** Owner: "OQ1 ->
  no keep it under .supervisor/roadmap.md as before. We will address later if the design turns out
  to be not necessary. Rationale: not that useful for external users." The prior decision stands;
  revisit if the design shows the file is unnecessary. The options below are kept as the record.
  Facts: only the curator reads or writes it
  (trims landed items; `.supervisor/roadmap.md` first, else root `ROADMAP.md`,
  `curator-procedures.md:24-25`); `planner` and `supervisor` never read it; nothing in `tests/` or
  `deploy` names it; the Roadmap intake item (commit 6c92f27) tells users to edit `ROADMAP.md` by
  hand and says the README names `.supervisor/roadmap.md` after Stage 4.
  - (a) Keep `ROADMAP.md` at the root as a human document, I5 format applied in place. For: visible
    on GitHub, in Finder, `ls` and Obsidian; hand edits per Roadmap intake stay natural; no rename,
    so no rebase conflict; the curator already finds it; other projects unchanged. Against:
    supersedes the three-horizons decision; entry paths make a human page denser; agents trim a root
    file.
  - (b) Move to `.supervisor/roadmap.md`, as currently decided. For: matches the decision and the
    roadmap's Stage 4 text; all project state in one tree. Against: hidden in Finder, `ls` and
    Obsidian (the research's D2 visibility check is still open); Roadmap intake's "edit by hand"
    points into a hidden directory; a project that gitignores `.supervisor/` loses its roadmap from
    version control; GitHub visitors of this repo lose a visible roadmap.
  - (c) Split: a short human roadmap at the root, the item list in `.supervisor/roadmap.md`. For:
    visible summary, structured list. Against: two files to keep in sync and a rule on which wins;
    contradicts "one ordered file" (`SKILL.md:16`, the three-horizons entry, `curator.md:21`); the
    most rule text.
  - Recommendation (overridden by the answer): (a). Stage 4 separates agent working state from
    human documentation; agents
    write research and plans, but people write and order the roadmap and agents only trim landed
    items. Keeping it costs two `SKILL.md` passages and one superseding entry; (b) hides the one
    file users are told to edit.
  - Depended on the answer: P2 (whole package) and the file P4's close-out trims, now
    `.supervisor/roadmap.md`. P1 and P3 proceeded.
  - Roadmap intake: under (a) its last sentence goes and its README section names `ROADMAP.md`;
    under (b) it names `.supervisor/roadmap.md` as written; under (c) it must say which file takes
    new items. Run Roadmap intake after Stage 4 lands so the README names the final path once.
- **OQ2. Is a fixture repo enough for "the procedure runs in another project"?** **Resolved
  2026-10-21: yes.** The fixture repo suffices (V1, V2, V4); P4 adds no real-project run. Affects
  P1's done-when and P4.
- **OQ3. Goal entries.** I5 has items name the `goal` entries they serve, but none exist. **Resolved
  2026-10-21: default.** No `Goals:` lines until the owner adds goals (`remember goal: ...`); the
  alternative (the curator writes goals for item 1 and Science artefacts in P2) is not chosen.
  Affects P2 only.
- **OQ4. Entry cap for P3.** **Resolved 2026-10-21: yes, and amended the same day: the five-entry
  cap is lifted for any `migrate` run** (any project migrating from an older layout; "migrations
  are a special case"), so the owner reviews all new entries (about 30 here) in one diff instead of
  six runs. Ordinary runs keep the cap. P1 states the exemption in `curator.md` and
  `curator-procedures.md`.

## Log

- 2026-10-21 planner: plan written (P1-P4), one review round, critic PASS; deferred: OQ1-OQ4 to the owner (P2 blocked on OQ1, OQ3)
- 2026-10-21 supervisor: OQ1-OQ4 answered by owner (OQ1: .supervisor/roadmap.md; OQ2 fixture; OQ3 default; OQ4 cap lifted for migration); P2 unblocked
- 2026-10-21 executor P1: done, 9031668 on memory-stage4 (pushed); critic PASS round 2 (C1-C3, C6 fixed; C4, C5, C7 rejected); migrate cap exemption made general (OQ4 amended); dev tag at 2.6+memory-stage4.1.g9031668 (V7 ok); deferred: V1 (needs a dev-tag session; fixture built), V6 test_deploy_version fix (predates P1, outside P1's files), item-1 bullet entry (clerk)
- 2026-10-21 executor V1: pass (simulated curator, fixture clone; dev tag dropped by owner); P1 text fixed in 460b58e (distil ## Approach; report stale names in moved working files; moved sources under working/); deferred: tool/preload exercise (no dev tag)
- 2026-10-21 executor P3: done, 460b58e on memory-stage4 (pushed); 11 files moved, 27 entries (25 decisions, 2 facts), docs/ = architecture.md, deploy.md; critic PASS round 2; deferred: owner entry review, reach-gap questions (REVIEW.md do-not-report list; planner approve-once rule), supersede candidates to P4, inbound refs in ROADMAP.md to P2
- 2026-10-21 supervisor: owner accepted P3's 27 entries; REVIEW.md do-not-report list extended; planner split rules written into planner.md
- 2026-10-21 executor P2: done, a61ca62 on memory-stage4 (pushed; A follow-up e7a6591); roadmap at .supervisor/roadmap.md in I5 format (item 1: 18 Decisions paths; Science artefacts Depends on by title; no Goals: lines), pack/README/architecture name it, V5 roadmap clean outside Stage 4, suite 365 passed; critic PASS round 1 (B-C1 fixed, B-C2 rejected); deferred: three entries with affects ROADMAP.md to P4 re-verify, store-readme roadmap.md line (P1-owned), child-plan clause reach to owner

## Todo

- [x] Owner answers OQ1-OQ4 (2026-10-21); OQ1 and OQ4 entries written and committed with the plan
- [x] `clerk` records item 1's unrecorded bullet (Data)
- [x] `executor` raises `VERSION` by one, runs the suite; `git-ops` commits plan and entries on
  `main`
- [x] Create worktree and branch `memory-stage4`; dev install under `supervisor-dev`; V7
- [x] P1 U1: researcher, planner, writer paths
- [x] P1 U2: curator migrate form, I2, I3, archive step, sweep glob
- [x] P1 U3: SKILL.md (I4, procedure list, prose), store-readme template
- [x] P1 U4: README, REVIEW.md, architecture.md
- [x] P1 glue: V5, V6, review, branch commit, dev install, V7 (dev install and V7 done in P1;
  the owner then dropped the dev tag)
- [x] Build the fixture; V1 on the dev tag (simulated curator; dev tag dropped)
- [x] P3: `curator migrate docs/` on this repo; owner reviews entries; branch commit
- [x] P3: supervisor switches to `.supervisor/working/plans/plan-memory-stage4.md`
- [x] P3: fix inbound references the report lists (outside the roadmap) (none editable: the
  only hits are in live `research-memory.md`, a dated record, and `.gitignore:9`, out of scope)
- [x] P2: `git mv` ROADMAP.md to `.supervisor/roadmap.md`; I5 format, pointers, Science artefacts,
  Roadmap intake sentence
- [x] P2: SKILL.md 15-16, 102-106; curator-procedures 24-31; README 225; architecture 80
- [x] P2 glue: V5 (roadmap), V6, review, branch commit (dev install skipped: the owner dropped
  the dev tag)
- [x] P4: V1-V7 batch (V2 full program, V3 this repo, V4 sweep) (V1, V2, V4 by simulated runs
  in fixture clones, V7 by `deploy --version` on the worktree; the owner dropped the dev tag)
- [x] P4: dev-tag close-out; owner checks diff; branch commit (simulated curator; owner diff
  check before landing)
- [ ] P4: rebase, squash merge on `main`, `VERSION` raised by one, suite, commit
- [ ] P4: `./deploy install`, `./deploy status`
- [ ] P4: with confirmation push; uninstall dev tag; remove worktree; delete branch

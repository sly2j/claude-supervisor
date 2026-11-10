# Plan: task cards replace the roadmap

Pointers are against `f5ebc96` (branch `feature/task-cards`); re-anchor by content.

## Open Questions

None.

## Goal

Replace the single ordered `.supervisor/roadmap.md` with task cards in `.supervisor/tasks/`, one
file per mid-term task, carrying ownership and coarse status, archived to `archive/tasks/`;
update every doc the change affects; migrate this repo's roadmap as the first user; ship as the
next major release.

Non-goals: a priority field; stage tracking on cards; auto-release of stale claims; pushed
claims as a cross-clone lock (see Improvements); a forced planner stage on pickup; a card
field for research artifacts; any `supervisor.md` or `git-ops.md` change; raising a lint cap;
deploying; pushing.

Expected change size: about 400 changed lines (additions plus deletions): pack 165 (one new
reference file, one new template), docs and README 30, tests 30, this repo's store and
`CLAUDE.md` 175 (nine cards, deferral cards at landing).

## Approach

Cards reuse the entry machinery (frontmatter, grep retrieval, archive by `git mv` with a finish
marker) and add only what a claimable item needs. All card rules sit in one new reference file,
`references/tasks.md`, because `SKILL.md` has two words of headroom; the pickup flow sits in the
`/pick-up` skill and in agent descriptions, because `supervisor.md` has none and the supervisor
reads descriptions and that skill, never `project-memory`. Docs change at the sentences the
change makes wrong or incomplete (D15).

Rejected: card rules inline in `SKILL.md` (over the word cap); a pickup rule in `supervisor.md`
(needs a rule cut, owner-only); a `task` agent or skill (new surface, no observed need); a
pytest lint of store content (see Improvements).

## Decisions

Binding from the brief (not reopened): location `.supervisor/tasks/` and `archive/tasks/`; a card
is one mid-term item whose plan carries stage status; `status: open | active | blocked` plus
`owner`, `since`, `plan`, `depends`, `decisions`; curator creates and archives, fixer claims and
changes status, scout lists; a claim is a fixer edit plus a `git-ops` commit
`chore(memory): claim <card>`; ordering by `depends:` only; a card per `deferred:` Log item;
`history.md` stays; roadmap `## Context` is dropped in the pack.

User answers (2026-11-10, the Log's `source: user` lines, not reopened): automatic migration of
`.supervisor/roadmap.md` only, a root `ROADMAP.md` gets a follow-up line (U1); item 2 is this
plan; a picked card routes as a typed prompt; close-out finishes a card the plan names (U2); docs
are part of the plan (U3, D15).

Lead decisions:

- D1 Name: `.supervisor/tasks/YYYY-MM-DD-<slug>.md`, date and slug rules as entries. The card
  name is the file stem; `depends:` cites card names, never paths, so archiving a dependency
  needs no repointing. Reason: same rule as entries, no collisions with archived cards.
- D2 A `summary:` key is added to the decided keys: the grep target entries already have, and
  the source of the one-line listing.
- D3 A `blocked` card states its reason in its `Notes:` line. A card may be blocked with no
  owner (waits on a decision, a condition, a date or access): the listing must not offer it as
  pickable.
- D4 `since:` is the date of the last status change; empty on an open card.
- D5 `owner:` is the branch the work will land from, written as briefed; the `/pick-up` default
  is `<type>/<card slug>` and the same name goes to the lead as its branch. Free text when the
  user says otherwise.
- D6 `plan:` is set at claim when the chosen route has a `planner` stage (the default plan
  path it will be briefed with, so no later edit), otherwise left empty. Close-out finds a card
  by its `plan:` value, by a `task <card>` argument, or by the plan naming it (card name or
  `summary:`) in its Goal or Scope Notes (U2). No card field for a research artifact: a
  following plan cites it, and a research-only card closes with
  `close-out <research path> task <card>`; `Notes:` can point to it.
- D6a A quick-tier card is not claimed: it is done in the current checkout and finished in the
  same session with `close-out task <card>`. Reason: D5's `owner:` is a branch, and a claim
  commit around a few-line fix costs more than the race it prevents.
- D6b A claim is compare-and-set: the claim edit replaces the text `status: open`; when `fixer`
  reports it not found (`fixer.md:45` already escalates that), `/pick-up` lists again. No lock.
- D7 New curator briefs: `task <text>` (create), `drop task <card>`,
  `close-out ... [task <card>]`, and `migrate ROADMAP.md` for a root file on request (U1).
  Reason: creation and dropping on the user's word are part of "curator creates and archives".
  The store's own roadmap needs no brief: D12 migrates it.
- D8 A finished card is archived whole; what the plan left over arrives as `deferred:` cards.
  Only a plan whose Scope Notes say it covers its card in part rewrites the card to the
  remaining gap and reopens it. Reason: keeps the roadmap's partial-landing rule in one line.
- D9 Cards do not count toward the five-entry cap; they are not entries.
- D10 Listing and claiming happen in the default-branch checkout, before the worktree is cut, so
  the branch carries the claimed card. Reach per store kind (one sentence in `tasks.md`): tracked,
  other clones once pushed (a linked worktree holds its branch's cards); local, this checkout
  only; externalized, shared live by every linked checkout.
- D11 `supervisor.md` and `git-ops.md` are untouched: the supervisor learns card duties from the
  `curator`, `fixer` and `scout` descriptions and the two skills, and `git-ops` already commits
  what `fixer` stages. Cost: status edits only on the user's word; the stale flag is the backstop.
- D12 Trigger: the curator preamble's "on every run" step, beside the README replacement, in the
  default-branch checkout only: a run that finds `.supervisor/roadmap.md` migrates it first and
  reports the cards, then moves it to `.supervisor/archive/working/plans/`, so the step runs once.
  `/pick-up` lists before any store write, so it dispatches `curator` `make this a project` first
  when that file exists.
- D13 Every item becomes one card: `blocked` with the reason in `Notes:` when it waits on a
  decision, condition, date or access, else `open`. Priority, effort, numbering and ordering
  notes are dropped; text that is not an item is reported `not migrated:`. Migration is exempt
  from the five-entry cap, as `migrate` is.
- D14 This repo's store is migrated by the executor applying the new procedure text by hand,
  since the deployed curator is still the old one. Likewise, before this plan's `curator
  close-out`, the landing lead applies the new close-out task step by hand: archive the
  `task-intake` card `met` with its `history.md` line, and open one card per `deferred:` Log
  item. A gap found in the procedure is fixed in the procedure.
- D15 Docs (U3): every doc the change makes wrong or incomplete is edited at the affected
  sentences only, no restructuring; the files and lines are under Outline, Docs. Author:
  `executor`, as a separate docs unit, no `writer` stage (`pack/agents/executor.md:25`, `:26`,
  `:49`). Style: for `README.md` and `docs/`, the four `domain: writing`
  entries in `.supervisor/memory/conventions/` (dated 2026-10-26 and 2026-10-30: what and why,
  reference voice, worked examples first, what users need); for pack text, `agent-authoring`.
  The executor passes those paths to the docs units and to their critic (domain `prose`).

Improvements weighed:

| Improvement | Verdict | Reason |
|---|---|---|
| `owner:` as branch, stale claim checkable | Not now | The branch is named at claim but cut later or never, so a missing branch would flag live claims; the 30-day inactivity rule stays. |
| Push the claim as a lock | Not now | Sessions sharing the default-branch checkout see a claim at once; the sync before a default-branch commit already surfaces an earlier pushed claim as a conflict. A push also publishes other unpushed commits and needs a standing `CLAUDE.md` permission; add it when a cross-clone race is observed. |
| Linted card size cap | Adopt the cap, not a store lint | Body at most 200 words, one sentence in `tasks.md`, kept by curator at write; the suite lints the pack, and other projects' stores never run it. The template is linted. |
| Claim this plan's own card (found) | Adopt | Exercises claim and archive on real data (user confirmed 2026-11-10). |

## Outline

### `pack/skills/project-memory/references/tasks.md` (new, about 40 lines; lines <= 100 chars)

Card shape, also the content of `templates/task.md`:

```
---
summary: <one line; the grep target>
status: open
owner:
since:
plan:
depends: []
decisions: []
---
Goal: one or two sentences.
Scope: what is in; the current gap only.
Done when: a checkable criterion.
Notes: questions left to the planner, pointers (optional).
```

Rules to state: name and slug (D1); body at most 200 words, no minor versions, `decisions:`
cites by path only entries that still bind; pickable means `status: open` and no `depends:`
name still present in `tasks/`; cards are listed and claimed in the default-branch checkout; the
reach sentence per store kind (D10); transitions:

| Transition | Who | Change |
|---|---|---|
| create | `curator` (`task`, close-out `deferred:`, roadmap migration) | new card, `open` or `blocked` |
| claim | `fixer` replacing `status: open` (D6b), then `git-ops` `chore(memory): claim <card>`; none for the quick tier (D6a) | `status: active`, `owner`, `since`, `plan` when the route has a planner stage |
| other status edits | `fixer`, on the user's word | block: `blocked`, reason in `Notes:`; unblock: `active` (`open` with no owner); release: `open`, `owner` and `plan` emptied; `since` per D4 |
| finish | `curator` close-out | `met: YYYY-MM-DD`, `git mv` to `archive/tasks/`, `history.md` line |
| drop | `curator` `drop task` | `dropped: YYYY-MM-DD`, `git mv`; report live cards that depend on it |

Archived cards are never edited or repointed.

### `pack/skills/project-memory/SKILL.md` (1378 of 1380 words; net change at most +2)

- Description: "the three horizons (goals, roadmap, plans)" becomes "(goals, tasks, plans)".
- Layout `:19-33`: the `roadmap.md` line becomes `tasks/  mid-term, one card per task`; add
  `tasks/` under `archive/`; `history.md` reads "one line per finished task or milestone".
- `:35`: entries still have no `status:` field; say that only task cards carry one.
- `:119-121`: add the task briefs to the curator procedure list.
- Horizons `:149-155`: the roadmap sentences (47 words) become a pointer of at most 35 words
  to `${CLAUDE_SKILL_DIR}/references/tasks.md`, keeping "never name a minor version".
- Budget: about 53 words removed, at most 55 added. Measure with `body_words`
  (`tests/test_pack_lint.py:84`); if over, cut restatements only, never a rule
  (`.supervisor/memory/decisions/2026-10-25-raising-a-pack-word-cap-is-owner-only.md`).

### `pack/skills/project-memory/templates/`

- `task.md`: the shape above. `store-readme.md:13-14`: `tasks/` line (cards, who writes
  them) replaces `roadmap.md`; `history.md` "one line per finished task"; `:16` "a status
  change is a move" is scoped to entries.

### `pack/skills/project-memory/references/curator-procedures.md` (no word cap; lines <= 100 chars)

- Preamble `:11-12`: "leave the roadmap item in place" becomes "leave the task card in place".
  After `:16-17` (README replacement), one sentence: on every run in the default-branch
  checkout, when `.supervisor/roadmap.md` exists, run the roadmap migration under Migrate first
  (D12); when a root `ROADMAP.md` exists, add `follow-up: curator migrate ROADMAP.md` to the
  report, as the legacy `docs/` proposal does (`:74-75`).
- Close-out step 6 `:37-53` becomes the task step, finished plans only: finish each live card
  whose `plan:` is this plan, that the brief names, or that the plan names in its Goal or Scope
  Notes (D6, D8); open one card per `deferred:` Log item unless a live card's `summary:` covers
  it, with a Notes pointer to the plan; repoint or drop `decisions:` citations in live cards as
  today's bullet at `:42-44`; append the `history.md` line in today's format with the card's
  summary and `decisions:`. The legacy "Decisions already made" bullet `:45-47` moves to Migrate.
  `close-out task <card>` with no path runs this step alone; a plan-less close-out (`:61-63`)
  also runs it for a card the brief names (`task <card>`).
- Audit `:79`, `:90`: citations in live cards replace roadmap citations; add the stale flag: an
  `active` card with no plan activity for 30 days (the plan's last Log line, else `since:`).
  Report `stale claim: <card> (<why>)`; never change the card.
- New sections `Task (task <text>)` and `Drop task`: per the transitions table.
- Migrate, new "For a legacy roadmap" block (`.supervisor/roadmap.md`, or `ROADMAP.md` when
  briefed): one card per item or remaining stage (D13); `depends:` from "Depends on" titles;
  legacy decision bullets become entries by the recording test; then the file moves (D12).
  Report the cards and the `not migrated:` lines.

### Agents and skills

- `pack/agents/curator.md` (311 of 400 words; at most +60): description `:3` "trim the roadmap"
  becomes "finish task cards", adds creating and dropping tasks and migrating a legacy
  `.supervisor/roadmap.md`; Scope `:16-21` lists the new briefs and replaces the
  roadmap edit sentence with "task cards only as the procedures say; a legacy roadmap only to
  migrate it"; `:27` "roadmaps" becomes "task cards"; Report `:45` "roadmap items removed"
  becomes "task cards opened, finished and dropped".
- `pack/agents/scout.md` (179 of 350; about +50): a Do bullet for a task list, frontmatter only,
  never bodies, one line per live card, grouped open, active, blocked; pickable first:
  `<card> | <status> | <owner or -> | needs: <unmet depends or -> | <summary>`; Report allows 30
  lines for it. Description gains "listing open task cards".
- `pack/agents/fixer.md` (348 of 350): body unchanged (`:45` escalates a missing target,
  `:34-36` stages store files); description (not in `body_words`) gains "task-card status edits".
- `pack/skills/pick-up/SKILL.md` (102 body words; skill cap 1380; about +95): argument and
  `argument-hint` become `[<plan path or task>]`, description gains "or pick a task". With no
  live plan, or when the user asks for a new task, in the default-branch checkout: when
  `.supervisor/roadmap.md` exists (Glob), dispatch `curator` `make this a project` first (it
  migrates, D12); one `scout` task list; the user picks; read the picked card (at most 200
  words); route its text exactly as the user's prompt would be routed (any lead or chain, or the
  quick tier); unless quick tier (D6a), brief `fixer` the claim as an exact edit replacing
  `status: open` (D5, D6, D6b), re-listing when `fixer` reports that text missing, and `git-ops`
  the claim commit (skipped for a local store); pass the card path, and the branch name to a
  lead, in the first brief.
- `pack/skills/close-out/SKILL.md:14`: add `task <card>` to the curator brief when the finished
  work has a card with an empty `plan:` (research-only, executor-only or quick-tier work).

### Docs (D15; every affected file, sentence-level edits)

- `README.md`: `:12` "a mid-term roadmap" becomes mid-term task cards; `:51` the `curator` line
  adds adding and archiving tasks; `:74` `/pick-up [<plan path or task>]`, "resume a plan, or pick
  a task when none is live"; `:177` `roadmap.md` becomes `tasks/` (one card per task); `:178`
  "keeps the roadmap current" becomes "finishes the task cards"; after `:179` one **Tasks:**
  bullet: `/pick-up` lists open tasks, claims the one you pick (quick fixes aside) and routes it
  as the same request typed in; one line of phrases to type, about 25 words ("show tasks", "add a
  task: ...", "block <task>: <reason>", "release <task>", "drop <task>"; finished tasks are in
  `.supervisor/history.md`); the reach clause per store kind (D10); a `.supervisor/roadmap.md`
  from an earlier version becomes tasks automatically. `:298` the tree line names `tasks/`.
- `docs/architecture.md`: inventory rows `:33` (`fixer`: task-card status edits), `:34`
  (`curator`: tasks in its list), `:36` (`scout`: task listing); `:66` close-out also finishes the
  plan's task card; `:70` curator's direct-dispatch list gains "add a task"; `:94` `tasks/` in
  the store description and `history.md` "one line per finished task"; `:116` skills row,
  `/pick-up [<plan path or task>]` and "or pick a task".
- `docs/workflow-lifecycle.md` (it quotes `/pick-up` wording, `:137`): `:29` close-out also
  finishes the work's task card; `:125` argument and the no-live-plan sentence: lists open
  tasks, claims the picked one (quick fixes aside) and routes it as the same request typed in.
- No change: `docs/local-memory.md` (`:3` already calls an externalized store "the same live
  store everywhere it is linked"; `:93` stays exact, since a claim is not committed in a
  git-excluded store and the external repo commits only at close-out and after waves,
  `repo-workflow/references/external-store.md:18-20`); `docs/context-engineering.md` and
  `docs/deploy.md` (nothing in them becomes wrong).
- `CLAUDE.md`: the two Context bullets (Slice 3). `CHANGELOG.md`: the `vX` line (Slice 4).
- Pack text users see (store README template, `/pick-up` report, scout listing, curator report
  lines) is in the files above.

## Slices

### 1. Cards exist: format, create, finish, drop, audit, migrate

Units: (a) `SKILL.md`, `references/tasks.md`, `templates/task.md`, `templates/store-readme.md`;
(b) `curator-procedures.md`; (c) `pack/agents/curator.md`; (d) `tests/test_pack_lint.py`.
- `test_memory_templates` (`tests/test_pack_lint.py:242`): `task.md` frontmatter -> keys
  exactly `summary, status, owner, since, plan, depends, decisions`; `status` is `open`; body at most 200 words.
- `test_curator_task_briefs`: `curator.md` Scope -> contains both `task <text>` and `drop task`.
Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py`.

### 2. Pickup flow and user docs

Units: (a) `scout.md`, `fixer.md`, `pick-up/SKILL.md`, `close-out/SKILL.md`; (b) `README.md`;
(c) `docs/architecture.md`, `docs/workflow-lifecycle.md`; (d) tests. Units (b) and (c) are the
docs units (D15).
- `test_routing_scope_in_description` (`ROUTING_SCOPE` `:166`): `scout` -> also "task cards";
  `fixer` -> also "task-card status".
- `test_pickup_claims`: `pick-up/SKILL.md` -> contains `chore(memory): claim`.
- check `docs`: `grep -n "pick-up \[" README.md docs/*.md` -> every hit reads
  `[<plan path or task>]`.
Checkpoint: `python3 -m pytest -q`; `git diff f5ebc96 --stat -- pack/agents/supervisor.md
pack/agents/git-ops.md` is empty; `grep -rni roadmap pack docs README.md | grep -vi migrat` hits
only `curator-procedures.md` and `pick-up/SKILL.md`.

### 3. This repo's store and `CLAUDE.md`

One unit, by hand per the new roadmap-migration text (D14), date prefix the day it runs.
Expected cards from `.supervisor/roadmap.md` (all `decisions:` paths there exist at `f5ebc96`):

| Item | Card slug | Status |
|---|---|---|
| 1 | `retrieval-automation` | `blocked`: waits for an observed missed-entry failure |
| 2 | `task-intake` | `active`, `owner: feature/task-cards`, `plan:` this plan |
| 3 | `program-logs-for-flat-plans` | `open` |
| 6 | `science-artefacts` | `blocked`: deferred by the owner; no `depends:` (the store it needed shipped) |
| 7 | `re-measure-harness-efficiency` | `blocked`: not before late November 2026 |
| 8 | `haiku-relay-for-codex-critic` | `blocked`: only if transcript visibility proves insufficient |
| 9 | `interpreter-path-for-codex` | `blocked`: only if the need shows up |
| 10 | `verify-alcf-preset` | `blocked`: needs live ALCF access |
| 12 | `global-installs-and-deploy-tool` | `blocked`: owner decision pending |

Each `blocked` reason goes in the card's `Notes:`. Then `git mv`
`roadmap.md` to `archive/working/plans/`, replace `.supervisor/README.md` from the template, and
add to `CLAUDE.md` the two Context bullets it lacks: the owner's style rule (bullet 6) and
"read `docs/architecture.md` before touching the pack" (bullet 3, folded into the
`agent-authoring` line). The other Context bullets duplicate `CLAUDE.md` or the pack.
- check `cards`: `ls .supervisor/tasks | wc -l` -> 9; each card's keys match the template and
  its body is at most 200 words (a throwaway shell loop, not a committed test).
- check `citations`: every `decisions:` path in the cards -> exists.
- check `roadmap gone`: `test ! -e .supervisor/roadmap.md` and the archived copy exists.
Checkpoint: the three checks, then `python3 -m pytest -q`.

### 4. Land as the next major release (after Todo 1-3; not an executor slice)

After Todo 1-3 are complete and the user's go: the landing lead applies the task step by hand
(D14), then `curator close-out` on the branch, then `repo-workflow` Landing. The squash commit on
`main` sets `VERSION` to the next `X.0` and adds the `CHANGELOG.md` line
`- **vX** (YYYY-MM-DD): ...` in the same commit; the branch never touches `VERSION`.
- check `own card`: `archive/tasks/` -> holds the `task-intake` card with `met:`; `tasks/` -> one
  card per `deferred:` Log item; `history.md` -> one new line for it.
Checkpoint: `python3 -m pytest -q` on `main` before the commit. Deploy and push wait for the
user's separate confirmation.

## Verification

In the worktree after slice 3: the slice 2 and 3 checkpoints pass. Read `tasks.md`, the task
step and `/pick-up` once as a fresh agent would and walk one card through create, claim, finish.
After the owner deploys: in a scratch project holding `.supervisor/roadmap.md` and a root `ROADMAP.md`, run `/pick-up` (the store roadmap becomes cards
unasked; `ROADMAP.md` stays, with one follow-up line), then "add a task", pick a small and a
planned card, and close both out, confirming the listing line, routing as a typed prompt, one
claim commit (none for the quick tier) and the archived cards.

## Risks

- `.supervisor/roadmap.md` changing on `main` during the work conflicts with its move at rebase;
  re-apply the change to the matching card.
- A card edited on the default branch (block, release) while its branch archives it can conflict
  at landing; status edits after the claim are rare by design.
- With no `supervisor.md` rule, an unprompted supervisor may skip the claim when the user starts
  a task in plain words. Observe before adding a rule (it would need an owner-approved cut).

## Scope Notes

- In: the files named in the Outline (docs per D15), this repo's store and `CLAUDE.md`, the
  release steps.
- Out: `supervisor.md`, `git-ops.md`, `deploy`, lint caps, the live routing check, deploy, push.
- Not reopened (`.supervisor/memory/decisions/`): the brief's binding items and the user
  answers; no word cap raised, no rule cut to fit (`2026-10-25-raising-a-pack-word-cap-is-owner-only.md`);
  curator and fixer never commit (`2026-10-24-git-ops-not-curator-or-clerk-commits.md`);
  `project-memory` names no repo (`2026-10-22-project-memory-rules-are-generic.md`); no new
  lifecycle skill (`2026-10-29-only-close-out-and-pick-up-ship-as-skills.md`); audit on request
  only (`2026-10-24-the-memory-audit-runs-only-on-request-a.md`). Close-out supersedes
  `2026-10-24-the-roadmap-stays-at-supervisor-roadmap.md`.

## Assumptions

- The supervisor routes card duties from agent descriptions and `/pick-up` without a body rule:
  checked by the post-deploy walk in Verification, not by the suite.
- `deploy` needs no change for a new store folder: `grep -n "roadmap\|tasks" deploy` is empty at
  `f5ebc96`; `tests/test_deploy_memory.py` passes unchanged.

## Log

- 2026-11-10 decision: roadmap migration is automatic; curator migrates `.supervisor/roadmap.md` or a root `ROADMAP.md` into task cards when it first finds one, unasked, and reports it; supersedes "migrate roadmap on request only"; source: user
- 2026-11-10 decision: roadmap item 2 (intake) is answered by this plan; its card is archived `met` at close-out; source: user
- 2026-11-10 decision: a picked card is routed exactly as a user prompt carrying its text (any lead or chain, or the quick tier); no forced planner stage; `plan:` is set only when a plan comes out of it; source: user
- 2026-11-10 decision: the migration runs from the curator preamble's every-run step, and `/pick-up` dispatches `curator` `make this a project` first when a roadmap file exists; source: lead
- 2026-11-10 decision: a quick-tier card is not claimed and is finished with `close-out task <card>`; no card field for research artifacts; source: lead
- 2026-11-10 decision: automatic migration applies only to `.supervisor/roadmap.md`; a root `ROADMAP.md` is not moved, and curator reports a one-line follow-up suggestion for it, as the legacy `docs/` migration does; narrows the earlier automatic-migration decision; source: user
- 2026-11-10 decision: at close-out curator also finishes a live card that the plan names in its Goal or Scope Notes (by card name or `summary:`), besides the `plan:` match and a `task <card>` brief; source: user
- 2026-11-10 decision: documentation is part of the plan: every doc the change affects (`README*`, `docs/`, `CLAUDE.md`, `CHANGELOG.md` at landing, the store README template, pack text users see) is updated with minimal sentence-level edits in good writing style; source: user
- 2026-11-10 decision: a claim is compare-and-set on `status: open`; the automatic migration runs only in the default-branch checkout; source: lead
- 2026-11-10 lead slice 1 (1a-1d): task-card format, curator procedures, curator.md and tests in the pack; deferred: none
- 2026-11-10 lead slice 2 (2a-2d): scout, fixer, /pick-up, /close-out, README and docs, routing-scope phrases; deferred: none
- 2026-11-10 lead slice 3: nine cards, roadmap archived, store README replaced, two CLAUDE.md bullets, checks green; deferred: none
- 2026-11-10 lead slice 4 (by hand, curator still old): task-intake card archived met, history.md line added; deferred: none (the landing, install and Todo 4 itself complete in the landing dispatch)

## Todo

- [x] 1a `SKILL.md` edits within the word budget; `references/tasks.md` (reach per store kind);
      `templates/task.md`; `store-readme.md`
- [x] 1b `curator-procedures.md`: preamble (task card wording, default-branch migration,
      `ROADMAP.md` follow-up), task step (incl. plan-named cards), audit stale flag, Task, Drop
      task, Migrate "For a legacy roadmap"
- [x] 1c `curator.md` description, Scope, Operating, Report
- [x] 1d `test_memory_templates` extension, `test_curator_task_briefs`
- [x] 2a `scout.md` (grouped listing), `fixer.md` description, `/pick-up` (roadmap guard, card
      read, routing as a prompt, compare-and-set claim unless quick tier), `/close-out`
- [x] 2b `README.md` lines per Outline, Docs, with the four convention entries (D15)
- [x] 2c `docs/architecture.md`, `docs/workflow-lifecycle.md` per Outline, Docs (D15)
- [x] 2d routing-scope phrases, `test_pickup_claims`; the `docs` check and the roadmap grep
- [x] 3 nine cards, roadmap archived, store README replaced, two `CLAUDE.md` bullets; the three
      checks
- [x] 4 (landing lead, before `curator close-out`) task step by hand: `task-intake` card
      archived `met`, deferral cards opened, `history.md` line (D14)

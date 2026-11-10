# Plan: pick up several cards in one worktree

Card: `2026-11-10-pick-up-several-cards-in-one-worktree`. Pointers taken at `ac6e2a6`.

## Goal

`/pick-up` accepts several cards and routes them as one request under at most one plan; a session
already in a linked worktree lists and claims there; README and docs say so.
Non-goals: close-out (already finishes every card whose `plan:` is the plan), landing rules,
agent files, `supervisor.md`. Expected change: about 30 changed lines in 6 files (a diff of about
90 lines); next minor.

## Approach

Edit `pick-up/SKILL.md`, `project-memory/references/tasks.md`, four doc mentions and one lint
test, one behaviour per slice. Rejected: claiming on the default branch from a worktree session
(a confined worktree cannot reach it; the branch would keep a stale open copy).

## Decisions

- D1 Several cards route as one prompt carrying all card texts (binding: a picked card routes as
  a typed prompt). A planner stage gives them one shared plan path; without one, `plan:` stays
  empty.
- D2 Cards in `$ARGUMENTS` (names or paths under `.supervisor/tasks/`) are the pick: the `scout`
  task list still runs (pickability, branch, worktree) but the user is not asked to pick. A path
  under `.supervisor/working/plans/` stays a plan path.
- D3 A `fixer` exact edit per card, then one commit `chore(memory): claim <card>, <card>`.
- D4 Default branch for several cards: `<type>/<first card slug>`; the user may name another.
- D5 A session already in a linked worktree lists and claims in it; `owner:` is its branch
  (`scout` reports branch and worktree; supervisor has no Bash). Tracked store: the claim commits
  on that branch and lands with it. The lead brief also names the worktree path, so `executor`
  works there and merges only when asked (`pack/skills/repo-workflow/SKILL.md:74-75`).
- D6 A worktree claim shows on the default branch only when the branch lands; accepted, since a
  claim is advisory (`2026-11-10-a-pushed-claim-is-advisory-not-a-lock.md`) and a worktree's store
  lands with its branch (`pack/skills/project-memory/SKILL.md:56`).
- D7 Claiming in a worktree whose branch still has a live plan: add no text, neither permission
  nor prohibition (owner, Q1).

## Outline

- `pack/skills/pick-up/SKILL.md`: `description`, `argument-hint` `"[<plan path> | <card>...]"`;
  `:12` (D2); `:20` adds "or in the linked worktree the session is in", its condition unchanged;
  `:22` list also reports branch and linked-worktree state; `:23-31` per D1, D3-D5, the brief
  carrying the card paths, the branch, and in a worktree its path.
- `pack/skills/project-memory/references/tasks.md`: `:14` shared `plan:`; `:18-19` keeps the
  default-branch rule and adds "a session already in a linked worktree lists and claims there, on
  its branch"; `:32` commit `chore(memory): claim <card>[, <card>]`.
- Docs: new argument form, "claims the cards you pick", worktree sentence in README `:180`.
- `tests/test_pack_lint.py:187-189` `test_pickup_claims`: add the assertions below.
- Gotchas: pack lines at most 100 characters; per D7, no wording on live plans.

## Slices

1. Several cards (D1-D4): `pick-up/SKILL.md` frontmatter, `:12`, `:23-31`; `tasks.md` `:14`,
   `:32`; README `:74`, `:180` first sentence; `workflow-lifecycle.md:125`; `architecture.md:116`.
   Tests (`test_pickup_claims`): `pick-up SKILL.md -> contains "one or more"`;
   `tasks.md -> contains "claim <card>[, <card>]"`. Checkpoint: `python3 -m pytest -q`.
2. Worktree claim (D5-D6): `pick-up/SKILL.md:20,22,27,31` worktree parts (`:27` owner);
   `tasks.md:18-19`; README `:180` worktree sentence.
   Tests (`test_pickup_claims`): `tasks.md -> contains "lists and claims there"`;
   `pick-up SKILL.md -> contains "linked worktree"`. Checkpoint: `python3 -m pytest -q`.
   All four phrases have zero hits at `ac6e2a6`.

## Verification

`python3 -m pytest -q` passes; `grep -n "plan path or task" README.md docs/*.md` is empty;
`git diff --stat main -- VERSION` is empty on the branch.

## Risks

- A local store does not exist in a linked worktree (`pack/skills/project-memory/SKILL.md:49-50`),
  so no card lists there; no new text.

## Scope Notes

- Out: close-out, deploying, pushing, the live routing check, agent files. Binding: D7, the card's
  `decisions:`; `VERSION` untouched on the branch, the landing commit raises y.

## Assumptions

- `scout` reports branch and linked-worktree state when asked, no `scout.md` edit needed;
  checked against `pack/agents/scout.md:19` ("Answer the question asked").

## Log

- 2026-11-10 planner: blocked (first pass; Q1 for owner); deferred: full plan until Q1 is answered
- 2026-11-10 decision: Q1 add no text (owner)
- 2026-11-10 planner: done (full plan; critic PASS round 1); deferred: none
- 2026-11-10 lead: done (both slices; pytest 600 passed; critic PASS round 1; branch ready, not landed pending close-out); deferred: landing and `VERSION` bump until curator close-out

## Todo

- [x] Slice 1 edits, tests and checkpoint
- [x] Slice 2 edits, tests and checkpoint
- [x] Verification

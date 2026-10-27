# Plan: test-residue cleanup (ledger directory, naming, teardown on `fixer`)

## Goal

Test artifacts left behind by R&D and execution (temp dirs, config files, profiles, tmux
sockets, venvs, background processes, remote files over ssh) get recorded in a per-agent ledger
directory and torn down by `fixer` after each program wave and at the end of every Mode 1 run,
local and remote, without user confirmation. Non-goals: hooks or `settings.json`, residue that
predates this feature, `deploy`. Expected size: about 150 lines in 12 files (new skill about 80).

## Approach

One new preloaded skill, `residue`, holds the whole mechanism (prevention, naming, ledger format,
teardown procedure); agent files get frontmatter preloads and one-line hooks. Rationale: the
brief's placement in `lead-loop` fails on repo facts (`lead-loop` has 27 words of cap headroom,
`supervisor.md` 1, `fixer.md` 15; workers never load `lead-loop`; `agent-authoring:53` puts a
procedure in a skill). Rejected: per-agent rules (duplication, no headroom); a shared ledger
file (race); the scratchpad as ledger (not shared across agents or sessions).

## Decisions

- D1 Ledger directory: `.supervisor/working/residue/` in the main checkout's store (never a
  worktree's copy), one file per writing unit, `<agent>-<id>.md`. Local-only, never staged or
  committed: the first writer appends `/.supervisor/working/residue/` to
  `$(git rev-parse --git-path info/exclude)` when `git check-ignore -q .supervisor/working/residue`
  fails (pattern: `repo-workflow` lines 68-70). A carve-out from the committed store
  (`2026-10-24-the-store-is-committed-in-the-branch-and.md`): residue is machine-local or
  reachable only from here, so other clones cannot act on it, and excluding it keeps every
  squash, rebase and store commit free of ledger churn.
- D2 Entry shape (data shape, see Outline): host, resource, `remove`, `check`, `needed-by`.
  `check` exits 0 once the resource is gone, so teardown verifies mechanically; remote entries
  carry full `ssh user@host '...'` commands, so no ssh rule is needed anywhere else.
- D3 Naming: every test artifact carries `sup-<id>-`, `<id>` a short random token the unit picks
  once (example `openssl rand -hex 3`) and reuses as its ledger file suffix.
- D4 Prevention: artifacts live in the session scratchpad or `mktemp -d`, and the unit stops
  processes and removes them in the same step once the result is captured; only an artifact a
  later stage or package needs survives, with a ledger entry written before the step ends.
- D5 Teardown runs on `fixer` (haiku), brief `teardown <dir> [done: <ids>]`: each eligible
  entry's `remove` runs verbatim, then `check`; success deletes the entry (and an emptied file),
  failure appends `failed: <date> <reason>` and keeps it. It runs nothing outside a ledger entry
  and refuses (reports as failed) a `remove` that targets `/`, `~`, `$HOME` or the project root,
  or uses `sudo`. Failed entries are skipped until the user asks for a retry.
- D6 Triggers, both in `supervisor.md`: the existing per-wave `fixer` also tears down entries
  whose `needed-by` package it just marked `done`; at the end of every Mode 1 run (plan or
  plan-less) a `fixer` `teardown` precedes any `curator` close-out, and the supervisor relays
  failures to the user once. Flat plans prune only at the end (no stage boundary in the flat
  flow).
- D7 One-off directories (no store, `project-memory`: they persist nothing) get no ledger:
  units tear down everything before reporting and list what they could not remove.
- D8 Preloads: `executor`, `executor-worker`, `researcher`, `researcher-worker`, `fixer`; not
  `writer`, `planner`, `critic`: no observed residue, and a clause needs an observed failure
  (`2026-10-24-edge-cases-sections-of-the-extraction.md`).
- D9 `git-safety` unchanged: its gates (`SKILL.md:10-19`) name git subcommands only, so recorded
  removals need no gate; D5 is the safety net.
- D10 `supervisor.md` stays at or under 1000 body words (headroom today: 1). The D6 insertions
  are at most 28 words (shapes in Outline); the executor trims the Mode 2 table examples at
  lines 27 and 29 (28 words), which restate agent descriptions the Agent tool already lists.
  Allowed without the owner (`2026-10-25-raising-a-pack-word-cap-is-owner-only.md`); if it
  still does not fit, stop and report instead of raising the cap or cutting a rule.
- D11 Landing: feature branch in a clean worktree, rebased on `main` immediately before the
  squash; `VERSION` bumps only in that squash on `main`, to what `main` holds then plus one,
  never a hardcoded number. A parallel v8.0 branch may touch `supervisor.md`, `lead-loop`,
  `fixer.md`, `docs/architecture.md`: re-test after the rebase; escalate overlapping conflicts.

## Outline

- `pack/skills/residue/SKILL.md` (new, under 350 body words; frontmatter per
  `pack/skills/python-env/SKILL.md:1-4`, `user-invocable: false` like `lead-loop`). Sections:
  Prevent (D4), Name (D3), Ledger (D1, D7, entry shape below), Teardown (D5: brief shape,
  procedure, report `residue: removed N, failed M` plus a line per failure, or `residue: none`).
  ```
  - host: local | user@host
    resource: <path | tmux socket or session | pid | venv>
    remove: <command run verbatim; a remote entry is a complete ssh command>
    check: <command that exits 0 once the resource is gone>
    needed-by: none | <package id>
  ```
- `pack/agents/{executor,executor-worker,researcher,researcher-worker,fixer}.md`: add
  `residue` to `skills:` (workers currently have no `skills:` key; add it). Body text unchanged
  except `fixer.md:22`, which gains the sentence `` `teardown <dir>`: per the `residue` skill. ``
  (fixer headroom 15 words).
- `pack/agents/supervisor.md:84-86`: append `, and runs `teardown` (`residue`) for packages it
  marked `done`` (10 words); `:88`: a new bullet before it, illustrative: `At a Mode 1 run's
  end, `fixer` `teardown` (`residue`) precedes any `curator` close-out; relay failures once.`
  (17 words); trims per D10. Invariant: 1000 words.
- `pack/skills/project-memory/SKILL.md:25-27` layout block gains a `residue/` line (local only,
  never archived); `:38-39` names who writes it (any preloader of `residue`) and that it is
  git-excluded, never staged or committed. Headroom 90 words.
  `pack/skills/project-memory/templates/store-readme.md:8-9`: mention `residue/` (local only).
- `tests/test_pack_lint.py`: two wording tests in the shape of lines 262-278.
- `docs/architecture.md`: Skills table row for `residue`; `fixer` row (line 33) adds "tears
  down recorded test residue"; lines 66 and 68 gain the teardown; `README.md:50` likewise.
- Gotcha: `body_words` (`tests/test_pack_lint.py:84-91`) counts fenced code and excludes
  frontmatter; the 100-char line rule exempts tables and fences only.

## Slices

1. Skill and preloads. Units: (a) `pack/skills/residue/SKILL.md`; (b) the five agent
   frontmatters plus the `fixer.md:22` sentence; (c) `tests/test_pack_lint.py`
   `test_residue_skill_preloaded[rel]`: for each of the five agents, `residue` in `skills` ->
   pass; `test_residue_skill_caps`: skill body words <= 350 -> pass.
   Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py`.
2. Triggers and store layout. Units: (a) `supervisor.md` per D6 and D10; (b) `project-memory`
   SKILL.md and template; (c) `tests/test_pack_lint.py` `test_teardown_wired[rel]`:
   `"teardown" in text` for `agents/supervisor.md` and `agents/fixer.md` -> pass.
   Checkpoint: `python3 -m pytest -q` and the lint's word count for `supervisor.md` <= 1000.
3. Docs sync. Units: (a) `docs/architecture.md`; (b) `README.md:50`. Docs only: the checkpoint
   and `git diff --stat` are the check. Checkpoint:
   `python3 -m pytest -q && ./deploy install --dry-run`.

## Verification

On the rebased branch: `python3 -m pytest -q` passes; `./deploy install --dry-run` lists
`skills/residue`; `git diff main --stat` touches only Outline files. Dry run: `fixer` `teardown
<scratch dir>` on a hand-written ledger: a `mktemp -d` entry (removed), one targeting `~` (failed).

## Risks

- Haiku `fixer` running `rm -rf` and `ssh ... rm` verbatim: bounded by D5; a wrong `remove`
  command written by an agent is the residual risk.
- A confined worktree (`supervisor.md:71-72`) cannot reach the main store; rare, not handled.
- Existing `.supervisor/README.md` files keep the old layout text (template is never re-copied).

## Scope Notes

- In: ledger directory, naming, prevention, per-wave pruning, close-out teardown on `fixer`,
  ssh hosts, doc and inventory sync, lint tests. Out: hooks or `settings.json`, pre-existing
  residue, `deploy`, `git-safety`, `lead-loop`, any file not in Outline.
- Binding user decisions, not to reopen: a directory of per-agent ledger files, never a shared
  file or relayed through reports; `fixer` teardown without confirmation, failures reported once,
  never silently retried; `sup-<id>-` naming on every test artifact.
- Constraints: `agent-authoring` for every pack edit; no cap raise (D10); `fixer` never commits
  (`2026-10-24-git-ops-not-curator-or-clerk-commits.md`); `git-safety` trailer only.

## Assumptions

- `git rev-parse --git-path info/exclude` resolves to the shared exclude file from a worktree;
  the executor checks it with one command in the worktree before writing the rule.

## Open Questions

None.

## Log

## Todo

- [x] Slice 1: `residue` skill, five preloads, `fixer` sentence, two lint tests; checkpoint
- [x] Slice 2: `supervisor.md` triggers and trims (<= 1000 words), `project-memory`, wiring test
- [x] Slice 3: `docs/architecture.md`, `README.md:50`; checkpoint; then Verification
- [x] Land per D11: rebase on `main`, re-test, squash with `VERSION` bump on `main`

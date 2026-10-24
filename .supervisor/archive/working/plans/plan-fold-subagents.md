# Plan: fold within the harness (next major version)

Release: the next major version, `X.0`. The branch `worktree-fold-subagents-review` lands by
squash-merge, which sets `X.0` per `repo-workflow`; another branch is also heading for a major,
so the number is fixed only at landing.
Research: `.supervisor/working/research/research-fold-subagents.md` (sections 3-4 for the numbers).
Line numbers below are as of commit c8094fb; `executor` re-checks them before editing.

## Goal

Make the harness cheaper on the paths the audit showed are mostly confirmation, without changing
its shape: (R2) `scope-critic` runs only when it has something to rule on or the artifact is big;
(R3) the `executor` lead implements a single unit itself; (R4) a named minimal Mode 1 path the
`supervisor` briefs deliberately; three `git-safety` fixes behind real stops; opt-in audit tooling
to re-measure; `docs/architecture.md` in sync and lint green.

Non-goals: a single-loop fold, merging leads, folding the Haiku tier or git into the supervisor,
dropping the supervisor's no-read rule, a golden end-to-end eval (R1), README changes, `VERSION`,
roadmap item 4 (the writer light path; D1 covers part of it, the rest stays a separate item).

Expected change size: about 120-160 changed lines across 8 files under `pack/` and `docs/`, one
new reference file (about 25 lines), one new script (about 400 lines, ported), a 30-line README
under `tools/audit/`, and one `.gitignore` line.

## Approach

Edit the shared protocol (`lead-loop`) once per feature and let agent files defer to it, so each
rule lives in one place. Put the git fixes in `git-safety` (989 words of headroom) rather than
`git-ops.md` (0 headroom), since `git-ops` preloads it. Put the worktree-landing procedure in a
`repo-workflow` reference file (the `git-safety/references/` pattern), since `repo-workflow` is at
its cap. Port the two working audit scripts into one stdlib script with an output scrub.

Rejected: making `Review: light` the minimal path (light already covers mechanical multi-file work
that fans out); a critic-side bloat flag for R2 (`critic.md` has 31 words of headroom); applying
R3 to `researcher` and `writer` (their single-worker defaults exist to keep raw sources and drafts
out of the lead's context, the article's discardable-context condition); a pytest smoke test for
the audit tool (the owner ruled it out of pytest); rewriting the feature branch to land from a
worktree (a detached squash needs no history rewrite).

## Decisions

### R2: when scope-critic runs

- D1. The condition is on the critic's findings table, not its verdict: `PASS` means only "no
  BLOCKING" (`pack/agents/critic.md`), so a PASS can carry SHOULD and NIT rows. `scope-critic` runs
  after a critic round when (a) the table has any row, or (b) the artifact exceeds the size bound.
  Otherwise the lead skips it and writes one decision-log line:
  `scope-critic skipped: round N, no findings, <size>`. That line is what the audit tool counts.
- D2. Size bound (the independent bloat check scope-critic also does): the change exceeds the
  plan's expected change size when a plan exists; otherwise more than 200 changed diff lines
  (code) or more than two pages of new prose (research, plan, prose). The lead measures it
  itself (`git diff --stat`, `wc -l`); no critic change. Tunable once the audit tool reports the
  skip rate.
- D3. Expected effect, from the baseline: round-1 PASS is executor 44/52, planner 7/15,
  researcher 4/12. PASS is an upper bound for "empty table", so the skip rate is at most 85% of
  executor first rounds and much lower elsewhere; review stays where it earns most (research and
  planning). The exact-condition rate is unmeasured, so slice 5 adds "round-1 empty findings table
  by lead" and "scope-critic dispatches per critic round" to the tool.
- D4. Rounds 2 and later keep "re-run `scope-critic` when the fixes added material"; it is the
  same rule (findings or size). `Review: light` becomes "one critic round, then scope-critic per
  step 4". `writer.md:45` and `:56` stop hard-coding "then `scope-critic`" and defer to lead-loop.

### R3: executor does single units itself

- D6. `lead-loop` section 2 drops "Fan-out is the default" and "Use N=1 only when the work
  genuinely cannot be split". New rule: dispatch workers when the work has two or more independent
  units, each worth a fresh context; for one unit, follow the agent file. The spawn-sparingly
  override (LL:34-35) stays, conditioned on "when the work splits". "Do work yourself only for
  integration glue" (LL:42-43) adds "and a single unit when your agent file says so".
- D7. `executor.md`: one unit (one disjoint file set, however many lines) is the lead's own work
  in the worktree, including tests for it; two or more disjoint units go to `executor-worker`s,
  one each. The rule at :45-46 ("implementation, tests and docs are separate units") is rewritten
  to apply only when a slice already has two or more units; "a unit that needs another's
  interface waits for it" stays. The description line says both. Difference from `planner`:
  planner never lets workers
  write the artifact (workers are read-only fact-finders); executor workers do write, and the
  executor may do all the work when there is one unit. Evidence: 30 of 38 duplicate-read files
  were under executor and 7 executor runs already went N=0.
- D8. `researcher` and `writer` keep their defaults (researcher.md:32 one worker for a single
  location; writer.md:34-36 one drafter). `lead-loop` names this in one sentence so the general
  rule and the lead files do not conflict. `planner` is unchanged.

### R4: the minimal path

- D10. A new brief line `Path: minimal` (absent means the full shape). Defined in `lead-loop`
  step 6 next to the `Review:` depths: one lead, the work expected to be one unit the lead does
  itself (R3), one `critic` round, `scope-critic` per step 4, stop; it implies `Review: light`.
  If the lead finds several disjoint units it fans out and says so in the report's Fan-out line.
  Rejected: `Review: minimal` (review depth and fan-out shape are different axes).
- D11. Supervisor routing rule (after the Mode 2 test, supervisor.md:34-37): brief `Path: minimal`
  when a request fails the Mode 2 test only on "cheap to undo" or "needs no design decision", and
  the outcome is specified and local (one subsystem, a few files). Mode 1 default stays full.
- D12. `supervisor.md` is at 1000/1000 words; R4 plus D16 need about 70 words. Roadmap item 2
  says cuts need the owner's approval, so the cuts are Open Question Q1. The executor applies
  the approved cuts in slice 3 and confirms `body_words` with `tests/test_pack_lint.py:83`.

### Git fixes (git-ops stays separate)

- D13. Own-session commits. `git-safety` SKILL.md:23-24 "Never amend a commit you did not create
  in this session" becomes: a commit any agent of the current supervisor session made is the
  session's own; amend or `reset` it only when the brief names its SHA and the operation, and
  never when it is pushed. The gate at :10-11 ("only when the user explicitly asked, as passed in
  your brief") gains the same clause. `git-ops.md:33-35` escalates a history rewrite "unless the
  brief names the target as this session's commit" (a wording swap, no net words).
- D14. Named staging. New `git-safety` rule next to the staging rules (:22, :26-27): when the
  brief names what to stage, other untracked or modified files never stop the run; commit with the
  briefed pathspec and list the untouched files in one report line. The secrets check applies to
  the staged paths. `git-ops.md` needs no new words (its :21-23 already stages explicit paths).
- D15. Landing from a confined worktree. New `pack/skills/repo-workflow/references/
  landing-from-worktree.md`; the skill's step 3 ("If there is none, stop") gains one sentence:
  when no checkout has the default branch, or the harness refuses commands against the parent
  checkout, follow the reference. Procedure (illustrative, in prose there): in the worktree,
  `git fetch origin`; step 2's rebase runs against `origin/<default>` (the branch is on no
  remote, so it is ungated) and the checks rerun; `git checkout --detach origin/<default>`;
  `git merge --squash <branch>`; `git add .supervisor`; bump `VERSION` (X.y repo); run the
  checks; the step-4 guard `git diff --cached --quiet <branch> -- . ':!VERSION'` applies
  unchanged; commit with the trailer; `git push origin HEAD:<default>` (fast-forward only, never
  `--force`; on rejection fetch, redo once, then stay detached, report the squash SHA and stop);
  push other remotes after origin in the same step; `git checkout <branch>`; report that the
  parent checkout needs `git pull --ff-only` and that the worktree was not removed. Without the
  push authorization in the brief (D16), stop before the push and report the squash SHA. Step 6
  "Never push" becomes "Never push, except the fast-forward push in the worktree landing".
  Satisfies the rebase-on-origin decision (the detached HEAD starts at fresh `origin/<default>`).
  `repo-workflow` is at 1300/1300; the compression is in the Outline.
- D16. `supervisor.md` tells `executor` and `git-ops` when the session is confined: one brief
  line `Confined to worktree: <path>; push to <default> authorized` whenever its environment
  names a worktree as the working directory and forbids the parent checkout. The push is
  outward-facing (supervisor.md:108-109), so the supervisor confirms it with the user before
  briefing the line (counted in D12).

### Tooling

- D18. One script `tools/audit/audit.py` (ported from the two scripts named in the Outline;
  probes are discarded), stdlib only, Python 3.9 syntax, run as
  `python3 -I tools/audit/audit.py`. Flags: `--root DIR` (repeatable; default both stores
  `~/.config/claude-supervisor/projects` and `~/.claude/projects`) and `--since YYYY-MM-DD`
  (to separate post-release sessions from the baseline corpus). Prints markdown tables to
  stdout, nothing else: critic round-1 PASS
  by lead, round-1 empty-table rate by lead, scope-critic dispatches per critic round, lead-tree
  tokens per run split lead / workers / reviewers, files read by two or more workers of one run,
  quick-tier ESCALATE rate, main-thread final context (median, max), plus corpus counts only.
- D19. Privacy: output lines carry counts, medians and 8-character session prefixes only; before
  printing, the script refuses (exit 2) any line matching `[/-](Users|home)[/-]` or containing a
  known `cwd`; briefs and handbacks are regex-matched, never printed. `.gitignore` gains
  `tools/audit/out/`, where the README tells the user to redirect stdout. No pytest test (owner
  decision); the checkpoint is a manual run. `tests/test_pack_lint.py` scans `pack/` only, so
  `tools/` is not linted; pytest collects `test_*.py` only, so `audit.py` is not collected.
- D20. `tools/audit/README.md` (about 30 lines): purpose, the run line with `-I`, flags, the
  privacy rule, and that outputs are never committed. Nothing in the main README.

### Sync

- D21. `docs/architecture.md` changes ride in the slice that changes the behaviour (lines in
  each slice's units); the `## Agents` table matches each agent file's description line.

## Outline

- `pack/skills/lead-loop/SKILL.md` (1148/1300 words, 127/300 lines; net +40 words at most)
  - :9-10 intro: "Workers do the bulk of split work"; scope-critic "when it runs".
  - :29-43 Fan-Out: D6 and D8 text; keep the wave and disjoint-files rules verbatim.
  - :51-59 step 4: D1 condition after the critic dispatch; keep "never in parallel".
  - :67-68 round 2+: unchanged sentence, add "per step 4".
  - :70-85 step 5: one line for the no-findings case (nothing to decide; record the skip).
  - :99-105 step 6 `Review:` bullets: D4 wording; new `Path: minimal` paragraph (D10).
  - :114-116 step 7 Fan-out line: add "or `Path: minimal`" to the N=0/1 sentence.
- `pack/agents/executor.md` (467/700): :3 description; :37-51 Fan-Out per D7; keep :47 literal.
- `pack/agents/writer.md` (498/700): :45-46, :56 drop "then `scope-critic`" (defer to lead-loop).
- `pack/agents/researcher.md`: no change (D8). `pack/agents/planner.md`: no change.
- `pack/agents/supervisor.md` (1000/1000): :14-15 Mode 1 sentence mentions the minimal path;
  after :37 the D11 rule; :66 brief fields add `Path: minimal`; D16 line near :60-68; cuts per Q1.
- `pack/skills/git-safety/SKILL.md` (311/1300): :10-11 gate clause (D13); :23-24 rewrite (D13);
  new rule next to the staging rules at :26-27 (D14).
- `pack/agents/git-ops.md` (350/350): :33-35 wording swap only (D13).
- `pack/skills/repo-workflow/SKILL.md` (1300/1300): :108-109 pointer sentence (D15); :129 "Never
  push" exception; compress about 40 words elsewhere without dropping a rule (candidates: the
  :65-67 worktree-cleanup sentence, :84-93 Sync With Origin phrasing). Pattern for the reference
  file:
  `pack/skills/git-safety/references/conflict-resolution.md` and `git-safety` SKILL.md:44.
- `pack/skills/repo-workflow/references/landing-from-worktree.md`: new, prose steps per D15.
- `tools/audit/audit.py`: new; ports `audit.py` (:46-55 dedup, :129-132 context, :188-194
  duplicate reads, :218 tree tokens, :219-227 ESCALATE) and `followup.py` (:20-25 verdict regex,
  :56-66 round numbering, :85-116 tables), both in
  `/private/tmp/claude-502/-Users-sjoosten-Work-claude-agents/5e3da4f9-a28b-4e3a-ba51-9ccfa362eb9c/scratchpad/logaudit/`
  (a session scratch directory; see Assumptions); argparse like `deploy:1603`;
  `encoding="utf-8"` on opens; `fromisoformat` in try/except (3.9 rejects odd fractions); drop
  the unused `hashlib`, the hard-coded scratch paths and the `5e3da4f9` skip.
- `tools/audit/README.md`: new. `.gitignore`: add `tools/audit/out/`.
- `docs/architecture.md`: per D21. `pack/skills/agent-authoring/SKILL.md`: no change (no
  agent added, removed or re-tiered).
- Invariants: lines in `pack/**/*.md` at most 100 characters (tables and fences exempt); every
  cap in `tests/test_pack_lint.py:21-24`; no pointer from `pack/` to this repo's memory or docs.

## Slices

Each slice ends with `python3 -m pytest -q tests/test_pack_lint.py` and the slice's grep checks.
Slices 1-3 edit `pack/skills/lead-loop/SKILL.md` in turn, so they run in order; units inside a
slice own disjoint files.

### Slice 1: conditional scope-critic (R2)

Delivers: leads skip `scope-critic` on a clean critic round within the size bound.
Units: (a) `lead-loop` steps 4-6 and intro; (b) `writer.md` :45-46, :56; (c) `architecture.md`
:18-21, :51-52, :56, :58, :78-80.
Tests:
- `lint caps`: `pytest tests/test_pack_lint.py` -> passes.
- `one home for the rule`: `grep -c "then \`scope-critic\`" pack/agents/writer.md` -> 0.
- `condition present`: `grep -n "no findings" pack/skills/lead-loop/SKILL.md` -> one hit in
  step 4 and one in step 5's skip line.
- `arch synced`: `grep -n "only job" docs/architecture.md` -> 0 (the :58 sentence now names
  both duties and the skip).
Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py`.

### Slice 2: executor does single units itself (R3)

Delivers: the executor lead implements one unit itself and fans out for two or more.
Units: (a) `lead-loop` section 2 and step 7 Fan-out line; (b) `executor.md` :3, :37-51;
(c) `architecture.md` :15-16, :31, :49.
Tests:
- `default removed`: `grep -c "Fan-out is the default" pack/skills/lead-loop/SKILL.md` -> 0.
- `literal kept`: `test_leads_name_worker_subagent_type` -> passes.
- `others unchanged`: `git diff --stat -- pack/agents/researcher.md pack/agents/writer.md
  pack/agents/planner.md` -> only writer.md (slice 1).
- `single unit named`: `grep -n "single unit\|one unit" pack/agents/executor.md` -> at least one
  hit in Fan-Out.
Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py`.

### Slice 3: the minimal path (R4) and the confinement brief line

Delivers: the supervisor can brief `Path: minimal`; leads know what it means.
Units: (a) `lead-loop` step 6 paragraph; (b) `supervisor.md` D11, D16, brief field, Mode 1
sentence, and the Q1 cuts; (c) `architecture.md` :10, :68-74, :80.
Tests:
- `field defined once`: `grep -n "Path: minimal" pack/skills/lead-loop/SKILL.md
  pack/agents/supervisor.md` -> one definition in lead-loop, routing and brief lines in supervisor.
- `cap held`: `python3 -I -c` with `body_words` from `tests/test_pack_lint.py:83` on
  supervisor.md -> at most 1000.
- `routing rule`: `grep -n "cheap to undo" pack/agents/supervisor.md` -> two hits (Mode 2 test
  and the minimal-path rule).
Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py`.

### Slice 4: git-safety fixes and worktree landing

Delivers: git-ops proceeds on the two staging and amend stops; a confined executor can land.
Units: (a) `git-safety/SKILL.md` D13, D14; (b) `git-ops.md` :33-35 swap; (c) `repo-workflow`
SKILL.md pointer, "Never push" exception, compression, plus the new reference file;
(d) `architecture.md` :41, :74.
Tests:
- `own-session clause`: `grep -n "session" pack/skills/git-safety/SKILL.md` -> hits at the gate
  and the amend rule.
- `named staging`: `grep -n "never stop" pack/skills/git-safety/SKILL.md` -> one hit.
- `tokens kept`: `test_default_branch_syncs_with_origin`, `test_git_ops_loads_git_safety` -> pass.
- `caps held`: git-ops at most 350 words, repo-workflow at most 1300 and 300 lines.
- `reference resolves`: `test -f pack/skills/repo-workflow/references/landing-from-worktree.md`
  and `grep -n "landing-from-worktree" pack/skills/repo-workflow/SKILL.md` -> one hit.
- `no force`: `grep -c "\-\-force" pack/skills/repo-workflow/references/landing-from-worktree.md`
  -> hits only in "never `--force`" phrasing.
Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py && ./deploy install --dry-run`.

### Slice 5: opt-in audit tooling

Delivers: `python3 -I tools/audit/audit.py` prints the baseline aggregates from the local store.
Units: (a) `tools/audit/audit.py`; (b) `tools/audit/README.md` and `.gitignore`.
Tests (manual, not pytest):
- `3.9 compiles`: `/usr/bin/python3 -I -m py_compile tools/audit/audit.py` -> exit 0.
- `no leak`: `python3 -I tools/audit/audit.py > tools/audit/out/run.md; echo $?` -> 0 with
  tables for all seven metrics; `grep -E '[/-](Users|home)[/-]' tools/audit/out/run.md` -> empty.
- `ignored output`: `git check-ignore -q tools/audit/out/run.md` -> exit 0.
- `not collected`: `python3 -m pytest -q --collect-only tools` -> "no tests ran".
Checkpoint: the `no leak` run plus `python3 -m pytest -q`.

## Verification

`python3 -m pytest -q` green (402 passed, 6 skipped before; `test_version` skips off `main`);
`./deploy install --dry-run` clean; `git diff --stat main -- VERSION README.md` empty;
`body_words` for every file in `pack/agents/` within its cap; the deployed instance (after
`./deploy install`, in a new session) runs one `Path: minimal` task and the executor's report shows
N=0 and `scope-critic skipped`.

## Risks

- Prose rules are judged by the model: a lead may still dispatch `scope-critic` on a clean round
  or spawn a worker for one unit. The audit tool is the check; expect indicative rates only.
- The size bound (D2) is a judgment call; a wrong number means scope-critic either rarely runs
  on clean rounds or always does. Tune after the first audit run following this release.
- The audit tool reads other projects' transcripts; the scrub guards output, not memory. Never
  add a flag that prints text.
- D13 lets a brief authorize amend/reset of a session commit; a wrong SHA in a brief is the
  remaining exposure. The "never when pushed" clause bounds it.

## Scope Notes

In scope: A-F of the brief. Out of scope (owner, `.supervisor/memory/decisions/
2026-10-24-keep-the-multi-agent-architecture.md`): single-loop fold, merging leads, folding the
Haiku tier or git into the supervisor, dropping the no-read rule, R1 eval, README changes.
Binding owner decisions `executor` must not reopen: `2026-10-24-next-major-folds-within-the-harness.md`
(R2-R4 happen), `2026-10-24-git-ops-stays-separate-fix-git-safety.md` (fixes 1-2, git-ops
separate), `2026-10-24-efficiency-scripts-are-opt-in-tooling.md` (never by default, outputs never
committed), `2026-10-23-rebase-on-origin-before-landing-on-main.md`,
`2026-10-23-only-git-ops-commits-memory-writes.md`, `2026-10-23-store-lives-in-the-branch.md`
(the worktree's store is its branch's memory; landing carries it). Baseline numbers:
`.supervisor/memory/facts/2026-10-24-efficiency-baseline-for-drift.md`. Pack changes go into
`pack/` with no pointer to this repo's memory or docs. `VERSION` untouched on the branch.

## Assumptions

- Line numbers in Outline match commit c8094fb; checked by `executor` with `grep -n` before editing.
- `/usr/bin/python3` is 3.9.6 without pytest (fact entry `2026-10-21-usr-bin-python3-has-no-
  pytest-check-3.md`); checked by `/usr/bin/python3 --version`.
- The harness refusal text for parent-checkout git commands is stable enough to recognize
  ("isolated in the worktree ... Refusing"); checked when the executor lands this branch.
- The two port sources still exist at the scratch path in the Outline; checked with `test -f`
  before slice 5. If they are gone, slice 5 is a rewrite from the metric list in D18 and the
  JSONL fields named in the research artifact, and the executor says so in its report.

## Open Questions

- Q1. Which `supervisor.md` sentences may be cut to make about 70 words of room (roadmap item 2
  requires owner approval)? Word counts by `body_words`: :91-94 project-detection parenthetical
  46, :52-54 ad-hoc review chain 31, :89-90 "curator and clerk never commit" 26, :67-68
  attribution 21. Recommended: :91-94 (the detection rule lives in `project-memory` and the
  supervisor dispatches `make this a project` without checking, per
  `2026-10-23-store-lives-in-the-branch.md`) plus :89-90 (lint enforces "never commit" in
  `curator.md` and `clerk.md`), 72 words. Fallback: :52-54 plus a trim of :67-68 that keeps the
  lint-required phrase "harness attribution reminders" (`tests/test_pack_lint.py:254-262`).

## Log

- 2026-10-24 planner: done; plan-fold-subagents.md written, one review round (critic PASS, scope-critic TRIM applied); deferred: Q1 supervisor.md cuts await owner approval
- 2026-10-24 decision: owner approved the plan incl. README lines 76/85; Q1 resolved by shortening 52-54/67-68 and compressing 89-94, no cap raise
- 2026-10-24 executor: done, slices 1-5 landed on worktree-fold-subagents-review (6 commits, 403 passed); deferred: deployed-instance `Path: minimal` check (needs `./deploy install` and a new session), rebase on main and squash-merge at close-out
- 2026-10-24 decision: owner loosened R2 to skip scope-critic on NIT-only rounds; live check skipped, land now

## Todo

- [x] S1a lead-loop: intro, step 4 condition, step 5 skip line, round-2 wording, Review bullets
- [x] S1b writer.md: :45-46, :56 defer to lead-loop
- [x] S1c architecture.md: diagram, steps, Review depths, "Why two critics?", cost
- [x] S1 checkpoint
- [x] S2a lead-loop: Fan-Out rewrite (D6, D8), step 7 Fan-out line
- [x] S2b executor.md: description and Fan-Out (D7), literal kept
- [x] S2c architecture.md: diagram fan-out, executor row, step 2
- [x] S2 checkpoint
- [x] S3a lead-loop: `Path: minimal` paragraph (D10)
- [x] S3b supervisor.md: routing rule, brief field, confinement line, approved cuts, cap check
- [x] S3c architecture.md: Mode 1 label, routing, cost
- [x] S3 checkpoint
- [x] S4a git-safety: gate clause, own-session amend rule, named-staging rule
- [x] S4b git-ops.md: :33-35 word-neutral swap
- [x] S4c repo-workflow: pointer, "Never push" exception, compression; new reference file
- [x] S4d architecture.md: git-ops row, landing sentence
- [x] S4 checkpoint incl. `./deploy install --dry-run`
- [x] S5a tools/audit/audit.py ported with the two new metrics, scrub, `--root`, `--since`
- [x] S5b tools/audit/README.md; `.gitignore` line
- [x] S5 manual checks
- [x] Verification; report the diff summary and the `no leak` run output line count

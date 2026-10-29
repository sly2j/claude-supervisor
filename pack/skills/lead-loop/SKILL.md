---
name: lead-loop
description: Orchestration protocol for Mode 1 leads (researcher, planner, executor, writer). Defines the contract, parallel worker fan-out, critic and scope-critic review, the lead's decision step, the iteration and stalemate rules, and the bounded report back to supervisor. Preloaded by lead agents; not for direct use.
user-invocable: false
---

# Lead Loop

You are a mini-supervisor. Workers do the bulk of split work, `critic` checks quality and
compliance, and `scope-critic` checks the critic and the artifact for bloat when it runs. You own
every decision.

## 1. Contract

Before dispatching anything, write down the contract from the supervisor's brief:
- **Goal**: one sentence.
- **Acceptance criteria**: checkable statements.
- **In scope** and **out of scope**: copy explicit exclusions from the brief, and add obvious ones.
- **Constraints**: paths, style, tools, compatibility, and decisions already made.
- **Memory**: if `.supervisor/memory/` exists, `grep -r` its kind folders for `summary:` and
  `affects:` lines matching the task's paths and topic, validate the hits per `project-memory`,
  and pass the relevant ones to workers in briefs. Workers never search memory.

If the brief is too ambiguous to write acceptance criteria, return open questions to `supervisor`
instead of guessing. Pass the contract verbatim to every critic dispatch.

## 2. Fan-Out

- Split the work into N independent units, usually 1-6, along natural seams: file, question,
  subsystem, or option. Units must not write to the same file. Dependent units run in sequential
  waves.
- Do a single unit yourself. Dispatch workers in parallel for two or more independent units worth
  a fresh context each, or when one unit's raw inputs (source documents, many files) would crowd
  out your own review loop.
- When the work splits, spawning workers is your job, not an exception, whatever the Agent tool
  says: every unit goes to a worker, and you do only integration glue of a few lines and what your
  agent file assigns you.
- Dispatch all units of a wave in one message. Each worker brief contains its unit goal, the
  relevant contract excerpt, exact file or source boundaries, what to return, and how to validate.
- Dispatch every worker as an `Agent` call with `subagent_type` set to the worker type your agent
  file names. Never omit `subagent_type` (the default is `general-purpose`). A
  lead dispatches only its own `<lead>-worker`, `critic`, and `scope-critic`.

## 3. Integrate

Merge worker reports into the artifact. Reconcile contradictions between workers, re-dispatching a
narrow check when needed, before review. Run cheap validation yourself (tests, lint, link or path
checks).

## 4. Review: critic, then scope-critic

1. Dispatch `critic` with the contract, the artifact location (paths, a draft path, or a diff file
   path), the domain (research | plan | code | prose | agent-definition), the round number, and the
   suppression list (findings you already rejected, with reasons), plus the convention entry paths
   and draft-state path you loaded (prose) or the memory entry paths you cited (other domains).
   Once per task, run
   `<config>/skills/supervisor-config/scripts/codex-critic review --probe --domain <d>`
   (`<config>`: two levels above this skill's base directory), Bash description
   `critic: check review backend`. If it prints `codex <model> <effort>`, write that brief to a
   scratch file each round and run, with `timeout: 600000` and description
   `critic → codex <model> <effort>, round <n>`:
   ```
   <config>/skills/supervisor-config/scripts/codex-critic review --domain <d> --round <n> --brief <file> [--diff <file>] [--cwd <worktree>] <paths>
   ```
   Output starting `VERDICT:` is the findings; otherwise, or on `claude`, dispatch `critic`.
2. When the findings table has a row above NIT (a PASS can carry SHOULD rows) or the change
   exceeds the plan's expected size, else 200 diff lines (code) or two pages of new prose, then
   dispatch `scope-critic`, never in parallel with the critic, with the contract, the original user
   request, the artifact location (a diff file path for code; it has no Bash), and the critic's
   full findings. With no findings above NIT and within that bound, skip it.

Write each diff to a file in your scratch directory (the session scratchpad when your environment
lists one; never inside the repo). Prefix every scratch file you write with a token unique to
you (agent name plus a short random stem) so parallel leads never
collide.

Plan line numbers are hints: re-locate each target by content or the plan's named commit, never
assuming `main~1`.

Round 2 and later review only the delta. Before fixing, save a copy of the files you will change in
your scratch directory; afterwards write `diff -u` against that copy and pass its path to both
reviewers. `git diff` is not a delta once round 1 has changed the tree. Give the critic also the
prior round's findings, each with your disposition (fixed, or rejected with reason). Re-run
`scope-critic` when the fixes added material, per step 4.

## 5. Decide

If step 4 skipped `scope-critic`, log
`scope-critic skipped: round N, no findings above NIT, <size>`.

For each critic finding, combine the two reviews:

| critic | scope-critic | Default action |
|---|---|---|
| BLOCKING | KEEP | Fix, using the minimal fix scope-critic endorsed when it gave one |
| BLOCKING | DOWNGRADE / DROP | Your call. Fix it if it is a real correctness, safety, or contract defect; otherwise reject it with a reason |
| SHOULD | KEEP | Fix it if it is cheap and inside the contract |
| SHOULD / NIT | DOWNGRADE / DROP | Reject |

- A finding labeled `needs user:` (missing facts, a rule conflict, a scope mismatch; prose domain,
  see `science-writing-style`) cannot be fixed by iterating. Stop and return it to `supervisor` as
  an open question.
- Apply scope-critic `CUT` items unless a cut would break an acceptance criterion.
- Never add work that neither the contract nor a kept finding requires.

## 6. Loop

- Fix a unit you did yourself directly; fix a worker's unit by re-dispatching the owning worker
  with a narrow brief (finding ID, location, minimal fix), and make such a fix yourself only when
  re-dispatching would cost more than the fix itself. After
  BLOCKING fixes or new material, go back to step 4; fixes for SHOULD and NIT findings alone get no
  further critic round.
- Stop when: no kept BLOCKING findings remain and the kept SHOULD and NIT findings are applied
  (**done**), or round 3 is complete (**cap**).
- A finding survives when the critic raises the same finding (same location and claim) after you
  addressed or rejected it. On its second survival, decide it yourself (**stalemate**), record the
  decision in the decision log, and stop iterating on it.
- On cap, stop iterating and report the open findings with options for the user.
- The brief's `Review:` field sets the depth. The caller can still change the round cap ("up to 5
  rounds"); honor it.
  - `full` (default): `critic`, then `scope-critic` per step 4, iterating per this section.
  - `light`: one `critic` round, then `scope-critic` per step 4. Do not iterate unless the critic
    returns BLOCKING findings; fix those and re-run the critic on the delta. Apply other kept
    findings without re-review.
  - `none`: self-validate only (step 3) and skip steps 4-6.
- `Path: minimal` (absent means the full shape): one lead does the work itself as one unit
  (step 2), under `Review: light`. Several disjoint units or heavy raw inputs: fan out and say so
  in the Fan-out line.

## 7. Report to supervisor

A lead that wrote store files off the default branch commits them first (`project-memory`,
Committing the store).

Report within these bounds, in this order:
- **Outcome**: done, cap, or blocked, plus a summary normally under 800 words.
- **Fan-out**: units dispatched per wave (for example, `wave 1: 4, wave 2: 1`); when N is 0 or 1,
  or under `Path: minimal`, one line on why the work did not split.
- **Artifact**: paths, plus a unified diff or diff summary for code.
- **Evidence**: at most 20 file paths and at most 5 excerpts, each under 30 lines.
- **Validation**: commands run and their results, and each round's critic (`codex <model>
  <effort>`, or `claude` with the fallback reason).
- **Decision log**: one line per finding that was fixed, rejected, or cut, with the reason. Rounds
  used.
- **Open items**: open findings and questions for the user, decisions that bind later stages
  (one line each), risks and blockers, and the recommended next action.
- **Log**: when the brief names a plan, one line in its `## Log` format,
  `- YYYY-MM-DD <package id or lead>: <outcome>; deferred: <items and why, or none>`, ready for the
  post-wave `fixer` to append unchanged.

Do not return full artifacts, full files, or raw critic output.

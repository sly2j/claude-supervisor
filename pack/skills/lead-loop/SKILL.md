---
name: lead-loop
description: Orchestration protocol for Mode 1 leads (researcher, planner, executor, writer). Defines the contract, parallel worker fan-out, critic and scope-critic review, the lead's decision step, the iteration and stalemate rules, and the bounded report back to supervisor. Preloaded by lead agents; not for direct use.
user-invocable: false
---

# Lead Loop

You are a mini-supervisor. Workers do the bulk of the work, `critic` checks quality and compliance, and `scope-critic` checks the critic and the artifact for bloat and scope creep. You own every decision.

## 1. Contract

Before dispatching anything, write down the contract from the supervisor's brief:
- **Goal**: one sentence.
- **Acceptance criteria**: checkable statements.
- **In scope** and **out of scope**: copy explicit exclusions from the brief, and add obvious ones.
- **Constraints**: paths, style, tools, compatibility, and decisions already made.

If the brief is too ambiguous to write acceptance criteria, return open questions to `supervisor` instead of guessing. Pass the contract verbatim to every critic dispatch.

## 2. Fan-Out

- Split the work into N independent units, usually 1-6. Units must not write to the same file. Dependent units run in sequential waves.
- Use N=1 when the work does not split cleanly. Do not split work just to parallelize it.
- Dispatch all units of a wave in one message. Each worker brief contains its unit goal, the relevant contract excerpt, exact file or source boundaries, what to return, and how to validate.
- Small integration glue (connecting outputs, fixing a seam) you may do yourself. If you find yourself doing a unit's work, dispatch it instead.

## 3. Integrate

Merge worker reports into the artifact. Reconcile contradictions between workers, re-dispatching a narrow check when needed, before review. Run cheap validation yourself (tests, lint, link or path checks).

## 4. Review: critic, then scope-critic

1. Dispatch `critic` with the contract, the artifact location (paths, diff range, or draft path), the domain (research | plan | code | prose | agent-definition), the round number, and the suppression list (findings you already rejected, with reasons).
2. Dispatch `scope-critic` with the contract, the original user request, the artifact location, and the critic's full findings. This runs after the critic, never in parallel with it.

Round 2 and later review only the delta: the changed regions plus the findings being closed. Re-run `scope-critic` when the fixes added material.

## 5. Decide

For each critic finding, combine the two reviews:

| critic | scope-critic | Default action |
|---|---|---|
| BLOCKING | KEEP | Fix, using the minimal fix scope-critic endorsed when it gave one |
| BLOCKING | DOWNGRADE / DROP | Your call. Fix it if it is a real correctness, safety, or contract defect; otherwise reject it with a reason |
| SHOULD | KEEP | Fix it if it is cheap and inside the contract |
| SHOULD / NIT | DOWNGRADE / DROP | Reject |

- A finding labeled `needs user:` (missing facts, a rule conflict, a scope mismatch) cannot be fixed by iterating. Stop and return it to `supervisor` as an open question.
- Apply scope-critic `CUT` items unless a cut would break an acceptance criterion.
- You may overrule either critic. Record every overrule with a one-line reason in the decision log.
- Never add work that neither the contract nor a kept finding requires.

## 6. Loop

- Fix by re-dispatching workers with narrow briefs (finding ID, location, minimal fix), or make the fix yourself when it is trivial. Then go back to step 4.
- Stop when: no kept BLOCKING findings remain (**done**); round 3 is complete (**cap**); or the same finding survives two consecutive rounds (**stalemate**).
- On cap or stalemate, stop iterating and report the open findings with options for the user. Typical options: accept as-is, provide the missing input, relax a constraint, or allow a broader change.
- The caller can change the cap ("draft only, no review" or "up to 5 rounds"). Honor it.

## 7. Report to supervisor

Report within these bounds, in this order:
- **Outcome**: done, cap, stalemate, or blocked, plus a summary normally under 800 words.
- **Artifact**: paths, plus a unified diff or diff summary for code.
- **Evidence**: at most 20 file paths and at most 5 excerpts, each under 30 lines.
- **Validation**: commands run and their results.
- **Decision log**: one line per finding that was fixed, rejected, or cut, with the reason. Rounds used.
- **Open items**: open findings and questions for the user, risks and blockers, and the recommended next action.

Do not return full artifacts, full files, or raw critic output.

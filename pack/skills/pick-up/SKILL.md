---
name: pick-up
description: Re-enter a plan or program after /clear or a new session with one read-only state check, a short report, and a proposed next step. Use when the user runs `/pick-up` or `/pick-up <plan path>`.
argument-hint: "[<plan path>]"
disable-model-invocation: true
---

# Pick up

Dispatch one `scout` plan-state call; never read the plan yourself.

- Target: the plan named in `$ARGUMENTS`, else `.supervisor/working/plans/`.
- Ask `scout` for the plan, its packages or open `## Todo`, the last Log lines and any pending
  questions.
- Report at most 10 lines: plan, packages or open `## Todo`, last Log lines, pending questions.
- Propose the next step and wait for the user:
  - packages remain: the next wave;
  - flat plan with open slices: `executor` on them;
  - `## Todo` complete: `/close-out`.
- With no live plan, say so and ask what to pick up.

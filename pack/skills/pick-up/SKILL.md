---
name: pick-up
description: Re-enter a plan or program after /clear or a new session with one read-only state check, a short report, and a proposed next step, or pick a task. Use when the user runs `/pick-up` or `/pick-up <plan path>`.
argument-hint: "[<plan path or task>]"
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
- With no live plan, or when the user asks for a new task, work in the default-branch checkout:
  - when `.supervisor/roadmap.md` exists (Glob), dispatch `curator` `make this a project` first;
  - dispatch one `scout` task list and let the user pick;
  - read the picked card (at most 200 words) and route its text exactly as the user's prompt
    would be routed (any lead or chain, or the quick tier);
  - unless quick tier (finish with `close-out task <card>`), brief `fixer` the claim
    as an exact edit replacing the text `status: open` with `status: active`, setting `owner`
    (the branch, default `<type>/<card slug>`), `since` (today) and `plan` (the default plan path
    the planner will be briefed with, only when the route has a planner stage); when `fixer`
    reports that text missing, list again; then `git-ops` the commit `chore(memory): claim <card>`
    (skipped for a local store);
  - pass the card path, and the branch name to a lead, in the first brief.

---
name: pick-up
description: Re-enter a plan or program after /clear or a new session with one read-only state check, a short report, and a proposed next step, or pick tasks. Use when the user runs `/pick-up`, `/pick-up <plan path>` or `/pick-up <card>...`.
argument-hint: "[<plan path> | <card>...]"
disable-model-invocation: true
---

# Pick up

Dispatch one `scout` plan-state call; never read the plan yourself.

- Target: the plan named in `$ARGUMENTS`, else `.supervisor/working/plans/`. Cards named in
  `$ARGUMENTS` (names or paths under `.supervisor/tasks/`) are the pick.
- Ask `scout` for the plan, its packages or open `## Todo`, the last Log lines and any pending
  questions.
- Report at most 10 lines: plan, packages or open `## Todo`, last Log lines, pending questions.
- Propose the next step and wait for the user:
  - packages remain: the next wave;
  - flat plan with open slices: `executor` on them;
  - `## Todo` complete: `/close-out`.
- With no live plan, or when the user asks for a new task, work in the default-branch checkout, or
  in the linked worktree the session is in:
  - when `.supervisor/roadmap.md` exists (Glob), dispatch `curator` `make this a project` first;
  - dispatch one `scout` task list, also reporting the branch and linked-worktree state, and let
    the user pick one or more cards (not asked when `$ARGUMENTS` names them);
  - read the picked cards (at most 200 words each) and route their texts as one prompt, exactly
    as the user's prompt would be routed (any lead or chain, or the quick tier); the planner
    stage gives the cards one shared plan path;
  - unless quick tier (finish with `close-out task <card>`), brief `fixer` one exact edit per
    card replacing the text `status: open` with `status: active`, setting `owner` (the
    branch, default `<type>/<first card slug>`, or the worktree's branch), `since` (today) and
    `plan` (the default plan path the planner will be briefed with, only when the route has a
    planner stage); when `fixer` reports that text missing, list again; then `git-ops` the
    commit `chore(memory): claim <card>[, <card>]` (skipped for a local store);
  - pass the card paths, and the branch name to a lead, in the first brief; in a worktree also
    its path.

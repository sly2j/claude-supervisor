# Workflow Lifecycle

This page follows one piece of work from the first prompt to `/clear`: what you type, what the supervisor answers, what sits on disk meanwhile, and when it is safe to clear the conversation and come back later. The pieces it ties together are described in [architecture.md](architecture.md) and [README](../README.md#how-it-works).

## The Lifecycle And The Three Sizes

Every piece of work walks the same path. You open with a request, add to it while agents run, answer questions or approve a plan when one is needed, and receive a result. You then close out: temporary artifacts are removed, what the project learned goes into memory, and finished plans are archived. The supervisor ends with a line that says whether you can `/clear` and how to pick the work up again.

How much of that path a task uses depends on its size.

| Size | What runs | On disk meanwhile | At close-out |
|---|---|---|---|
| Small | One quick specialist or one lead, no plan file | Only the changed files | Test leftovers removed; memory updated only if there was something to record |
| Medium | One lead with a plan or research file, then the work | The plan or research file in `.supervisor/working/`, a worktree for code changes | Leftovers removed, decisions recorded, plan and research archived |
| Large | A program (a plan split into work packages), run in waves, often over several sessions | The parent plan with each package's state, child plans, worktrees | After each wave, leftovers of finished packages removed and the plan committed; at the end, full close-out |

## Prompts And Answers

The rows below generalize what users typed in real sessions. None of the prompts is a required form; the supervisor routes on intent.

**Open.** Say what you want, the constraints, and whether to push. "Fix the typo in README; push when done." "Check how deploy registers profiles, then start planning." On a small task the supervisor answers with a one-liner such as "Waiting on `fixer`". On a medium or large one it says which lead it dispatched.

**Mid-course additions.** Type new facts or rules while agents run: "also remember that rule", "once done, commit and push". The supervisor folds them into the running work or relays them to the lead. Pushing is authorized this way, in the opening prompt, or by answering its question.

**Questions and plan approval.** Leads cannot ask you anything directly, so the supervisor collects their questions into one batch, each with a recommended answer. Reply "all as proposed", or correct the ones you disagree with; referring to them by number works: "1 yes, 3 use the shorter name". A plan comes back with its path, a summary and its open decisions; approve it, or answer with changes. Medium plans are approved once. A large program needs one approval of the parent plan; child plans come back only for major design decisions.

**Result.** Every answer leads with the outcome. It then names who did what, what was validated, anything worth knowing, and a next step. For a small task that is often the whole exchange.

**Close-out.** Close-out does not start by itself: type `/close-out` when the work is done. If a plan is still open, it says so and stops. Otherwise it removes test leftovers, records what the work taught in the memory store, archives finished plans and research, and commits the memory changes. If a removal was blocked, `/close-out retry` tries again (see [Temporary Artifacts](#temporary-artifacts)).

**End.** The answer closes with a state line:

```
Session state: <closed out | wave N booked>; residue <removed | N failed>; store <committed | uncommitted | not stored>; safe to /clear, resume with "<prompt>"
```

- The first field says where the work stands: `closed out`, or `wave N booked` in a program. A wave is booked when its results are written into the plan file and committed.
- `residue` says whether test leftovers were removed, or how many removals failed.
- `store` says whether the memory changes were committed, are still uncommitted, or have no store to go into (`not stored`, see [Without A Memory Store](#without-a-memory-store)).

When stopping would lose something, the line reads instead:

```
Session state: <state>; not safe to /clear: <why>
```

The resume prompt is `/pick-up <plan path>` when a plan is live, otherwise a sentence stating the next task. In a program the line also appears after every booked wave, not only at the end. If it is missing, ask for it.

| Step | You type | The supervisor answers |
|---|---|---|
| Open | The task, constraints, push authorization | One-liner, or the dispatched lead |
| Add-ons | New facts or rules, any time | Folded in or relayed |
| Questions | "all as proposed", or numbers | The re-run stage, or the next question batch |
| Plan approval | "approved", or changes | Execution starts; progress per wave in a program |
| Result | Usually nothing; "ship it", "commit and push" | Outcome, who did what, validation, next step |
| Close-out | `/close-out` | Recorded and archived entries, `Run yourself:` if anything is left, the state line |

## Example: A Medium Task

An illustrative exchange, shortened. The `Session state:` line is the exact format; the rest is typical wording.

```
You:        the export script should take --json. Plan it, then build it; push when done.
Supervisor: Dispatched planner.
Supervisor: Plan: .supervisor/working/plans/plan-export-json.md. Add a --json flag
            next to the CSV writer, with a test. Questions:
            1. Write JSON to stdout unless --output is given? Recommended: yes.
            2. Keep CSV as the default? Recommended: yes.
You:        1 yes, 2 as proposed. Approved.
Supervisor: Plan updated with your answers and approved. Next: executor on both items.
You:        /clear
You:        /pick-up .supervisor/working/plans/plan-export-json.md
Supervisor: Plan approved, two open items, no pending questions. Next: executor on both. Go?
You:        go
Supervisor: Done: the export script takes --json; CSV stays the default.
            executor made the change in a worktree, tests pass, pushed to origin.
You:        /close-out
Supervisor: Recorded 1 decision; archived the plan.
            Session state: closed out; residue removed; store committed; safe to /clear, resume with "document --json in the README"
You:        /clear
```

## Temporary Artifacts

- **Worktrees.** Code changes run in a worktree under `.claude/worktrees/`. The agent that lands the change removes it.
- **Residue.** Residue is what tests leave behind: temporary directories, config files, tmux sockets, venvs, background processes, files on ssh hosts. Each item is listed in the residue ledger, `.supervisor/working/residue/`, which git ignores, and removed at the end of the work (in a program, after each wave for the packages that are done). You see only the items that could not be removed.
- **Plans and research.** They stay in `.supervisor/working/` while the work is open, and `curator` moves them to `.supervisor/archive/working/` at close-out.

**A failed removal.** Claude Code's permission system sometimes refuses a removal, for example a recursive delete of a large build directory. The item then stays in the ledger, and its `remove` command appears in the `Run yourself:` block described next. Run that command yourself, then `/close-out retry`: it runs every listed removal again, checks that each item is gone, and drops it from the ledger.

## Run Yourself

Some steps only you can run: a push you did not authorize, a removal Claude Code blocked, a deploy to another profile, a step in an account or UI. The supervisor collects them in one block at the end of its answer, headed `Run yourself:`. Shell commands appear verbatim in a fenced block; manual steps take one line each.

````
Run yourself:
```
rm -rf /tmp/claude-1002/.../sup-3fa9c1-build
```
Drag the figures into the pull request description.
````

Everything you need to do is in that block. A push is not on the list when you authorized it: in the opening prompt, in a message while agents were running, or by answering "push origin then public?". Agents always run authorized pushes; you run only the ones you held back.

## Clearing And Compacting

`/clear` ends the conversation and starts a new session. Everything on disk survives: the memory store, plans and research in `.supervisor/working/`, the residue ledger, worktrees and branches, and git history. These do not survive:

- the conversation itself, including a finished step whose result is not yet written into the plan file (the state line says `not safe to /clear` then);
- an unanswered batch of questions, and any `not stored:` note (see [Without A Memory Store](#without-a-memory-store)) or lesson proposal you have not answered;
- results from agents still running.

The cheapest places to clear, in order:

1. **After close-out and its commit.** All state is on disk or archived.
2. **After a booked wave in a program.** The plan file holds everything the next session needs; nothing is waiting on your answer.
3. **After plan approval, once the plan is on disk.** Start the new session with `/pick-up <plan path>`, or `/pick-up` to find it.

The `Session state:` line is the signal: it says `safe to /clear` or `not safe to /clear` with the reason.

`/compact` summarizes the conversation inside the same session; `/clear` empties it. A long session degrades before it runs out of room, and a summary carries the old context's momentum forward (see [context engineering](context-engineering.md#the-problem)); at a safe point, prefer `/clear` and `/pick-up`. Reserve `/compact` for mid-wave moments where clearing would lose something.

## Resuming

`/pick-up [<plan path>]` rebuilds your place from the plan file. It reads the plan you name, or finds the live one in `.supervisor/working/plans/`, and reports in at most ten lines: the plan, its packages or open items, the last log lines and any pending questions. It then proposes the next step and waits for your go: the next wave for a program, `executor` on the open parts of a flat plan, or `/close-out` when the work is finished. With no live plan it says so and asks what to pick up.

With no plan file, as in a small task, state the task in a sentence, as the state line's resume prompt does.

## Without A Memory Store

A directory is a project when it is inside a git repository, or when it or a directory above it holds `.supervisor/`, `.claude/`, `CLAUDE.md` or `AGENTS.md`; your home directory and what is above it never count. Anywhere else is a one-off: nothing is persisted and you are not asked. Anything an agent would have stored is reported once, as `not stored: no project store here; say *remember* to keep it`.

There is no residue ledger either: agents remove what they made and list in their report anything they could not remove. The state line reads `store not stored`, and after `/clear` there is no plan to pick up.

To make the directory a project, say "remember ...", "make this a project", or run `/close-out`, which creates the store. To end a one-off without storing anything, `/clear`.

<!-- Maintainers: this page quotes wording from the pack (the state line, the `Run yourself:` block, `/close-out` and `/pick-up`); update it when that wording changes. -->

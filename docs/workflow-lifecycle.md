# Workflow Lifecycle

This page follows one piece of work from the first prompt to `/clear`: what you type, what the supervisor answers, what sits on disk meanwhile, and when it is safe to clear the conversation and come back later. The pieces it ties together are described in [architecture.md](architecture.md) and [README](../README.md#how-it-works).

## The Lifecycle And The Three Sizes

Every piece of work walks the same path. You open with a request, add to it while agents run, answer questions or approve a plan when one is needed, and receive a result. You then close out: temporary artifacts are removed, what the project learned goes into memory, and finished plans are archived. The supervisor ends with a line that says whether you can `/clear` and how to pick the work up again.

How much of that path a task uses depends on its size.

| Size | What runs | On disk meanwhile | Close-out |
|---|---|---|---|
| Small | One quick specialist (Mode 2), or a single lead with no plan | Nothing but the changed files; test residue, if any, is in the ledger | Residue teardown. `curator` runs only if the work left a research artifact or a decision |
| Medium | One lead cycle: research, a flat plan, or a written artifact, then execution | A plan or research file in `.supervisor/working/`, a worktree for code changes | One residue teardown, then `curator` distills decisions and archives the plan and research |
| Large | A program: work packages run in waves, often across several sessions | The parent plan with each package's status and log, child plans, worktrees, the residue ledger | After each wave, teardown for finished packages and a plan-state commit. When every package is done, teardown, then `curator` close-out |

## Prompts And Answers

The rows below generalize what users typed in real sessions. None of the prompts is a required form; the supervisor routes on intent.

**Open.** Say what you want, the constraints, and whether to push. "Fix the typo in README; push when done." "Check how deploy registers profiles, then start planning." On a small task the supervisor answers with a one-liner such as "Waiting on `fixer`". On a medium or large one it says which lead it dispatched.

**Mid-course additions.** Type new facts or rules while agents run: "also remember that rule", "once done, commit and push". The supervisor folds them into the running work or relays them to the lead. Pushing is authorized this way, in the opening prompt, or by answering its question.

**Questions and plan approval.** Leads cannot ask you anything directly, so the supervisor batches their questions into a numbered list, each with its best guess. Reply "all as proposed" or correct by number: "1 yes, 3 use the shorter name". A plan comes back with its path, a summary and its open decisions; approve it, or answer with changes. Medium plans are approved once. A large program needs one approval of the parent plan; child plans come back only for major design decisions.

**Result.** Every answer leads with the outcome. It then names who did what, what was validated, anything worth knowing, and a next step. For a small task that is often the whole exchange.

**Close-out.** Close-out runs when the work is finished, but it has needed a typed nudge in practice, in many phrasings. Use `/close-out`. If a plan is still open it stops and says so; otherwise it tears down residue, has `curator` record and archive, and commits the memory changes. After a harness-blocked teardown, `/close-out retry` re-checks the failed entries (see the next section).

**End.** The answer closes with a state line:

```
Session state: <closed out | wave N booked>; residue <removed | N failed>; store <committed | uncommitted | not stored>; safe to /clear, resume with "<prompt>"
```

or, when stopping would lose something:

```
Session state: <state>; not safe to /clear: <why>
```

The resume prompt is `/pick-up <plan path>` when a plan is live, otherwise a sentence stating the next task. In a program the line also appears after every fully booked wave, not only at the end. If it is missing, ask for it.

| Step | You type | The supervisor answers |
|---|---|---|
| Open | The task, constraints, push authorization | One-liner, or the dispatched lead |
| Add-ons | New facts or rules, any time | Folded in or relayed |
| Questions | "all as proposed", or numbers | The re-run stage, or the next question batch |
| Plan approval | "approved", or changes | Execution starts; progress per wave in a program |
| Result | Usually nothing; "ship it", "commit and push" | Outcome, who did what, validation, next step |
| Close-out | `/close-out` | Recorded and archived entries, `Run yourself:` if anything is left, the state line |

## Temporary Artifacts

- **Session scratchpad.** Each session has its own scratch directory for briefs, diffs and logs. It is not cleaned by the pack; the operating system removes it eventually. Anything that must outlive a step is recorded in the residue ledger instead.
- **Worktrees.** Code changes run in a worktree under `.claude/worktrees/`. The agent that lands the change removes it.
- **Residue ledger.** Test artifacts (temporary directories, config files, tmux sockets, venvs, background processes, files on ssh hosts) are recorded one entry each in `.supervisor/working/residue/`, which git ignores. `fixer` tears them down after each wave for packages that are done, and again when the plan or run ends, before close-out. Each entry has a `remove` command and a `check`; the entry is deleted when the check passes.
- **Plans and research.** They stay in `.supervisor/working/` while the work is open, and `curator` moves them to `.supervisor/archive/working/` at close-out.

**A failed teardown.** The Claude Code harness sometimes refuses a removal outright, for example a recursive delete of a large scratch build. The entry then stays in the ledger marked `failed:`, and `fixer`'s report names the entry's `remove` command. Run that command yourself, then `/close-out retry`: the retry reruns each failed entry's `remove` and `check`, and the entry is deleted once the check passes. The failed command appears in the `Run yourself:` block described next.

## Run Yourself

Some steps only you can run: a push you did not authorize, a removal the harness blocked, a deploy to another profile, a step in an account or UI. The supervisor collects them in one block at the end of its answer, headed `Run yourself:`. Shell commands appear verbatim in a fenced block; manual steps take one line each.

````
Run yourself:
```
rm -rf /tmp/claude-1002/.../sup-3fa9c1-build
```
Drag the figures into the pull request description.
````

Nothing you need to do is asked for in prose elsewhere in the answer, so the block is the place to look. A push is not on the list when you authorized it: in the opening prompt, in a message while agents were running, or by answering "push origin then public?". Agents always run authorized pushes; you run only the ones you held back.

## Clearing And Compacting

`/clear` ends the conversation and starts a new session. Everything on disk survives: the memory store, plans and research in `.supervisor/working/`, residue ledgers, worktrees and branches, and git history. These do not survive:

- the conversation itself, including a lead's report that `fixer` has not yet appended to the plan log;
- an unanswered batch of questions, and any `not stored:` note or lesson proposal you have not answered;
- results from agents still running;
- the old session scratchpad as a working location. New agents write to the new session's scratchpad, and old files stay behind.

The cheapest places to clear, in order:

1. **After close-out and its commit.** All state is on disk or archived.
2. **After a booked wave in a program.** The plan log and status are updated, teardown for finished packages has run, the plan state is committed, and no package is waiting on your answer. The next session needs only a plan-state read.
3. **After plan approval, once the plan is on disk.** A flat plan has no automatic re-entry, so start the new session with `/pick-up <plan path>`, or `/pick-up` to find it.

Unsafe moments: mid-wave, between a lead's report and the plan log update, while a question batch is pending, and before a `not stored:` note or lesson proposal is answered. The `Session state:` line is the signal: it says `safe to /clear` or `not safe to /clear` with the reason.

`/compact` summarizes the conversation inside the same session and keeps the invoked skills attached, within a token budget per skill. `/clear` empties it. A long session degrades before it runs out of room, and a summary carries the old context's momentum forward (see [context engineering](context-engineering.md#the-problem)); at a safe point, prefer `/clear` and `/pick-up`. Reserve `/compact` for mid-wave moments where clearing would lose something.

## Resuming

`/pick-up [<plan path>]` rebuilds your place from the plan file. It asks `scout` for one plan-state read, of the plan you name or otherwise of `.supervisor/working/plans/`, and reports in at most ten lines: the plan, the packages or open `## Todo` items, the last log lines and any pending questions. It then proposes the next step and waits for your go: the next wave for a program, `executor` on the open slices of a flat plan, or `/close-out` when the work is finished. With no live plan it says so and asks what to pick up.

A program and a flat plan resume the same way. With no plan file, which is the small-task case, there is nothing to read back: state the task in a sentence, as the state line's resume prompt does.

## Without A Memory Store

In a directory that is not a project (a one-off folder outside git, with no `.supervisor/`, `.claude/`, `CLAUDE.md` or `AGENTS.md` here or above), nothing is persisted and you are not asked. A would-be store write is reported once, as `not stored: no project store here; say *remember* to keep it`.

There is no residue ledger either. Agents remove what they made before reporting and list anything they could not remove, so a failed removal appears only in that report. After `/clear`, only your files, git, and Claude Code's own transcripts and scratchpads remain; the state line reads `store not stored`, and there is no plan to pick up.

To make the directory a project, say "remember ...", "make this a project", or run `/close-out`, which creates the store. Inside a git repository you are asked first whether the store is tracked (committed with the repo) or local (git-excluded). To end a one-off without storing anything, `/clear`.

This page quotes wording from the pack (the state line, the `Run yourself:` block, the two skills) and must be updated when that wording changes.

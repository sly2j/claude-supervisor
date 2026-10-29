---
name: close-out
description: Close out the session's work by tearing down residue, archiving finished plans and artifacts into the store, committing it, and saying whether /clear is safe. Use when the user runs `/close-out` or `/close-out retry`.
argument-hint: "[retry]"
disable-model-invocation: true
---

# Close out

If a plan is still open (packages not `done`, or `## Todo` not complete), print the `Session state:`
line as `not safe to /clear` with the reason, and stop. Otherwise run these steps in order.

1. Brief `fixer` `teardown`; `teardown retry` when `$ARGUMENTS` contains `retry`.
2. Brief `curator` `close-out <path>` per finished plan or working artifact, `record` for a bare
   decision. In a one-off (no store), `curator` first creates the store (`make this a project`);
   inside git, ask the user once: tracked or local.
3. Brief `git-ops` `chore(memory): ...` for the staged paths `curator` and `fixer` report.
4. If anything remains for the user, end with one block headed `Run yourself:`: shell commands
   verbatim in a fenced block (copy a failed teardown entry's `remove` command from `fixer`'s
   report), manual steps one line each.
5. Print the last line, from what the agents reported:

```
Session state: <closed out | wave N booked>; residue <removed | N failed>; store <committed | uncommitted | not stored>; safe to /clear, resume with "<prompt>"
```

or `Session state: <state>; not safe to /clear: <why>`. The resume prompt is `/pick-up <plan path>`
when a plan is live, else the next task.

# Writing procedures

Used by `writer`, `writer-worker` and `critic` on prose. Style rules live in
`science-writing-style` and `presentation-style`; this file covers the project's writing
conventions and the per-draft state.

## Draft state

One file per draft, `.supervisor/working/writing/<key>.md`, copied from
the skill's `templates/draft-state.md`. It holds the draft's Session Decisions and its
Pending Verification. Only `writer` writes it, apart from `curator migrate` and the archive moves.

- `<key>`: the draft path relative to the project root (no leading `./`), `/` replaced by `--`:
  `proposal/body.tex` -> `proposal--body.tex`. `file:` holds the path exactly.
- A draft outside the root: `file: <host>:/abs/path` (`<host>` from `hostname -s`); the key drops
  the `:` and turns `/` into `--`: `polaris:/home/me/doc.tex` -> `polaris--home--me--doc.tex`.
- In a one-off (SKILL.md) there is no state file: `writer` keeps Session Decisions and Pending
  Verification in its run, lists them in its report with the `not stored:` line, and does not ask
  where to store them.
- Create and update the file only with the user's approval of each item. Date each Session
  Decision, name the section when it is local, and word it so a worker can apply it exactly.

## Precedence

Highest first:

1. Hard-floor rules in the style skill. Never overridden.
2. Active `convention` entries with `domain: writing` whose `affects:` is empty or covers the draft
   (the draft path, or a directory above it).
3. The draft's Session Decisions.
4. Author samples.
5. Overridable defaults in the style skill.

- A Session Decision that names a convention suspends it for that draft once the user approved it;
  it never suspends a hard floor.
- Pending Verification is per draft and non-binding. It never suppresses a finding; a critic may
  raise a matching pattern as minor with a `watchlist` note.
- A critic suppresses a finding that a convention or Session Decision covers (unless a hard floor
  is violated) and reports each suppression with its source: the entry file or the decision line.

## Worker and critic procedures

The lead's brief gives the draft-state path or `none`, the active conventions (each with its entry
path) and Session Decisions, and the style skill. Then:

- Use only what the brief gives; search neither memory nor `working/`, nor list the store.
  `none` means no state. A critic with no lead runs the first two Lead procedures itself.
- Apply the conventions and Session Decisions exactly as given. A `writer-worker` enforces a
  Pending Verification item only when the lead turns it into an explicit instruction.
- Never edit draft state or memory entries.

## Lead procedures

Before dispatching:

- Compute the key and read the draft's state file if it exists.
- `grep -r` `.supervisor/memory/conventions/` for `domain: writing`, keep the entries whose
  `affects:` is empty or covers the draft, and validate them per `SKILL.md`. Pass a stale one
  marked as unverified and name it in your report.
- Pass workers and the critic the inputs listed above, and flag to the user any conflict between
  the request and a convention.

After a draft is accepted or the loop stops, run the promotion checkpoint. For each deviation from
skill defaults preserved across rounds (recurring Pending Verification items are optional), give:

- `pattern observed:` short description plus example text from the draft
- `suggested convention:` the summary line and the wording
- `affects:` draft paths or directories to scope it, or empty for project-wide
- `override that preserved it:` the convention, Session Decision or author-sample anchor

The user confirms or rejects each candidate individually. Return the approved ones in your report
as `convention` entries to write: logged by `fixer` as `decision:` lines in a program, briefed to
`curator record` after a single-stage run. Write no entries.

When the user resolves a repeated finding by suspending a rule for one draft, record it as a
Session Decision naming the rule (entry file or style rule).

Archiving: when the user says the draft is done, propose `curator archive <state path>` in the
report. `curator` moves the state file to `.supervisor/archive/working/writing/` (also at
close-out of the program that owns the draft); the move is the whole status change.

## Legacy `docs/writing-rules.md`

A project with this file has not moved to the store. Do not apply or edit it. Before
dispatching, return one open question proposing `curator migrate docs/writing-rules.md`
(procedure in `references/curator-procedures.md`); with no project (SKILL.md), propose `make this
a project`, then `curator migrate docs/writing-rules.md`.

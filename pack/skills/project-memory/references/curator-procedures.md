# Curator procedures

Run by `curator`. Entry format, paths and the supersede step are in SKILL.md. Run the idle-plan
sweep on every run, after the brief's own procedure. The five-entry cap, unless the brief says
otherwise, counts every step; `migrate` is exempt. When the cap would cut entries, leave the
roadmap item in place, skip step 7, and report what remains as
`follow-up: curator close-out <plan path>`. Each `git mv` below uses plain `mv` instead without
git, or for a move into `.supervisor/` when it is gitignored (SKILL.md).

## Close-out (`close-out <plan path>`)

1. Read the `summary:` lines of `.supervisor/memory/*/`, then the plan: Scope Notes, Assumptions,
   Log, Decisions.
2. Collect candidates: user decisions and binding lead decisions not yet stored; facts verified in
   the program, each with a source; goals met or dropped; lessons, as proposals only.
3. For each candidate, grep `summary:` and `affects:` across `memory/*/` for neighbours, then
   choose one: new entry, supersede the neighbour (one step, per SKILL.md), or no-op. Merge
   duplicates or contradictory entries on one subject (from step 1) by superseding the older (the
   newer gains `supersedes:`). Stop at five new entries.
4. For each goal the plan finished, add `met: YYYY-MM-DD` (or `dropped:`), `git add` it, then
   `git mv` it to `archive/memory/goals/`.
5. Re-verify every entry in `memory/` that fails the staleness check in SKILL.md: confirm it by
   updating `verified:` to today, or supersede it.
6. Roadmap step, finished plans only. Open `.supervisor/roadmap.md`, else the project root's
   `ROADMAP.md`.
   - Remove the items, or the stages of an item, whose scope the plan covered (named in its
     title, Goal or Scope Notes).
   - For each removed item, record each legacy "Decisions already made" bullet not yet in memory
     as one `decision` entry (one entry per bullet) with `source: <roadmap path> item <n>, <date>`.
   - Append one line to `.supervisor/history.md` per removed item or stage group, in the
     SKILL.md format, high-level only, with the removed item's or stage's `Decisions:` paths (and
     the paths of any entries just recorded) in its `decisions:` field. Create the file with the
     heading `# History` on first use.
7. Archive step. `git mv` the plan and its child plans to `.supervisor/archive/working/plans/`
   and its research to `.supervisor/archive/working/research/`, keeping each file name. Move the
   draft state of the program's drafts to `.supervisor/archive/working/writing/`.

A close-out of an unfinished plan (the answer to an idle-plan proposal) skips step 6 and marks no
goal `met`.

## Idle-plan sweep

List each `.supervisor/working/plans/plan-*.md` whose last `## Log` line is dated more than 30
days ago. When its log is empty, use the plan's last commit date,
`git log -1 --format=%cs -- <plan>` (file mtime without git or when `.supervisor/` is
gitignored). Report each as "archive or keep?" with both follow-ups: archive is a
`curator close-out <plan>`; keep is a `clerk` brief appending `- <date> user: kept active` to the
plan's `## Log`. Never move a file.

Legacy proposal: when `docs/` holds `plan-*.md` or `research-*.md`, here or under `docs/archive/`,
add `follow-up: curator migrate docs/` to the report.

## Record (`record <decision text> from <report>`)

Write one entry per user decision or approved writing convention in the brief, a `convention` for
a writing convention, else a `decision`: `source` is the report's plan or path (else
`user <date>`); `affects` as the report gives it. Check neighbours as in close-out step 3.

## Remember (`remember <text>`)

Pick the kind from the text (a kind named in the brief does not bind): an aim is a `goal`, a
rule a `convention`, a stated choice a `decision`, anything else a `fact`. Write the entry with
`source: user <date>`. Check neighbours as in close-out step 3.

## Forget (`forget <text>`)

Find the entry by `summary:`. Supersede it with an entry recording the retraction (`source: user
<date>`); a goal gets `dropped: <date>` instead. Either way add the line to the old file, then
move it to `archive/memory/<kind>/`. Never delete a file.

## Make this a project (`make this a project`)

When no project root exists, create `.supervisor/` with its README per SKILL.md in the current
directory. Write no entries.

## Migrate (`migrate <path>`)

For `migrate docs/`:
- Live: `git mv` each `docs/plan-*.md` to `.supervisor/working/plans/` and each
  `docs/research-*.md` to `.supervisor/working/research/`, same name. Write no entries.
- Spent: for each `docs/archive/plan-*.md` and `docs/archive/research-*.md`, write one `decision`
  or `fact` entry per one still in force (`## Approach`, `## Decisions`, `## Scope Notes`, decided
  Open Questions, research conclusions), checking neighbours as in close-out step 3, with `source:
  .supervisor/archive/working/<plans|research>/<name>#<section>`; then `git mv` the file there.
  Move a file only after its entries exist. Propose lessons only.
- Every other `docs/` file stays; remove `docs/archive/` once empty.
- Report the moved paths, the entries written, and files outside `.supervisor/memory/`,
  `.supervisor/archive/` and `history.md` that still name a moved file (grep by name), then
  `recorded N`.

For a legacy writing rules file, skipping Standing Rules and Session Decisions already migrated
(check neighbours as in close-out step 3):
- Each Standing Rule bullet becomes one `convention` entry (`domain: writing`, `source:
  .supervisor/archive/working/writing/writing-rules.md`).
- Each Session Decision Log entry becomes a Session Decision in the draft-state file under
  `.supervisor/working/writing/` for the path part of its identifier, keyed as
  `references/writing.md` defines (create the file from the template when missing). When that
  path no longer exists, move the file to `archive/working/writing/` at once.
- Return each Pending Verification item as a promote-or-drop proposal.
- Then `git mv` the file to `.supervisor/archive/working/writing/writing-rules.md`.

## Archive (`archive <draft-state path>`)

`git mv` the state file to `.supervisor/archive/working/writing/`, keeping its name.

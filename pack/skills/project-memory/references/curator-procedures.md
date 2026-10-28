# Curator procedures

Run by `curator`. Entry format, paths and the supersede step are in SKILL.md. Run the idle-plan
sweep on every run, after the brief's own procedure. The five-entry cap, unless the brief says
otherwise, counts every step; `migrate` and `audit` are exempt, and retires (SKILL.md) do not
count. Before staging any entry, check it against Entry text and the recording test (SKILL.md):
grep the delivered work for its rule (test b), and rewrite it until it passes. The slug is cut at
the last word boundary within 40 characters, and a trailing stopword (a, an, the, and, or, of, to,
in, for, is) is dropped. A run that moves a file repoints, in the same run, every `source:` in
`memory/` that names it (grep by file name).
When the cap would cut entries, leave the roadmap item in place, skip step 7, and report what
remains as `follow-up: curator close-out <plan path>`. Without git, or when the store is
git-excluded (`git check-ignore -q <project root>/.supervisor` succeeds), nothing is staged: every
archive move here and in SKILL.md uses plain `mv` and skips `git add`, and the report says
`not staged: store untracked`.

## Close-out (`close-out <plan path>`)

1. Read the `summary:` lines of `.supervisor/memory/*/`, then the plan: Scope Notes, Assumptions,
   Log, Decisions.
2. Collect candidates that pass the recording test (SKILL.md): user decisions and binding lead
   decisions not yet stored, including the plan Log's `decision:` lines (an approved writing
   convention becomes a `convention`); facts verified in the program, each with a source; goals
   met or dropped; lessons, as proposals only.
3. For each candidate, find neighbours by grepping `summary:` and `affects:` across `memory/*/`
   and by `affects:` overlap with the paths the plan changed, then choose one: new entry,
   supersede the neighbour (one step, per SKILL.md), retire a neighbour (SKILL.md), or no-op. When
   two entries record one decision (from step 1), supersede the older (the newer gains
   `supersedes:`). Stop at five new entries.
4. For each goal the plan finished, add `met: YYYY-MM-DD` (or `dropped:`), `git add` it, then
   `git mv` it to `archive/memory/goals/`. Retire (SKILL.md) each lesson whose named fix the plan
   landed.
5. Re-verify every entry in `memory/` that fails the staleness check in SKILL.md: confirm it by
   updating `verified:` to today, or supersede it.
6. Roadmap step, finished plans only. Open `.supervisor/roadmap.md`, else the project root's
   `ROADMAP.md`.
   - Remove the items, or the stages of an item, whose scope the plan covered (named in its
     title, Goal or Scope Notes).
   - For an item the plan covered only in part, rewrite its Background to state only the
     remaining gap. In every remaining item, repoint citations of superseded entries to their
     replacements and drop citations of retired entries (their `superseded by:` names a path
     outside `.supervisor/memory/`).
   - For each removed item, record each legacy "Decisions already made" bullet not yet in memory
     that passes the recording test (SKILL.md) as one `decision` entry (one entry per bullet,
     none consolidated) with `source: <roadmap path> item <n>, <date>`.
   - Append one line to `.supervisor/history.md` per removed item or stage group, never
     rewriting earlier lines, as `- YYYY-MM-DD <version or commit> <item title>; goals: <paths or
     none>; plan: <archived plan path>; decisions: <paths>`, high-level only, with the removed
     item's or stage's `Decisions:` paths (and the paths of any entries just recorded) in its
     `decisions:` field. Create the file with the
     heading `# History` on first use.
7. Archive step. `git mv` the plan and its child plans to `.supervisor/archive/working/plans/`
   and its research to `.supervisor/archive/working/research/`, keeping each file name. Move the
   draft state of the program's drafts to `.supervisor/archive/working/writing/`.

A close-out of an unfinished plan (the answer to an idle-plan proposal) skips step 6 and marks no
goal `met`.

A plan-less run's close-out (`close-out <working artifact path>`) runs steps 1 to 3 and 5, reading
that artifact in place of the plan, then `git mv`s it to the matching `archive/working/` folder as
in step 7.

## Idle-plan sweep

List each `.supervisor/working/plans/plan-*.md` whose last `## Log` line is dated more than 30
days ago. When its log is empty, use the plan's last commit date,
`git log -1 --format=%cs -- <plan>` (file mtime without git or when the store is
git-excluded). Report each as "archive or keep?" with both follow-ups: archive is a
`curator close-out <plan>`; keep is a `fixer` brief appending `- <date> user: kept active` to the
plan's `## Log`. Never move a file.

Legacy proposal: when `docs/` holds `plan-*.md` or `research-*.md`, here or under `docs/archive/`,
add `follow-up: curator migrate docs/` to the report.

## Audit (`audit`)

Run on request. For every entry in `memory/` and every entry citation in the roadmap, apply the
recording test, Entry text and the staleness check (SKILL.md), resolve every `source:` and
`affects:` path (repoint a moved `source:`), then choose one outcome:
- keep, updating `verified:` when re-checked;
- retire (SKILL.md);
- supersede: the entry is stale, fails Entry text, has an `affects:` path that does not resolve,
  or is the older of two entries that record one decision or contradict each other;
- drop: a one-off that binds nothing after its plan closed. Add `dropped: audit <date>` and
  `git mv` it to `archive/memory/<kind>/` with no replacement (not Forget, which writes a
  retraction).

Fix roadmap citations as in close-out step 6. The audit never merges entries. Propose changes to
lessons and goals to the user; never retire or drop them, except a lesson whose named fix has
landed, which is retired. Report counts per outcome and
one line per kind of cut.

## Record (`record <decision text> from <report>`)

Write one entry per user decision or approved writing convention in the brief, a `convention` for
a writing convention, else a `decision`: `source` is the report's plan or path (else
`user <date>`); `affects` as the report gives it. Apply the recording test and check neighbours
as in close-out step 3.

## Remember (`remember <text>`)

Pick the kind from the text (a kind named in the brief does not bind): an aim is a `goal`, a
rule a `convention`, a stated choice a `decision`, anything else a `fact`. Write the entry with
`source: user <date>`. Apply the recording test and check neighbours as in close-out step 3.

## Forget (`forget <text>`)

Find the entry by `summary:`. Supersede it with an entry recording the retraction (`source: user
<date>`); a goal gets `dropped: <date>` instead. Either way add the line to the old file, then
move it to `archive/memory/<kind>/`. Never delete a file.

## Make this a project (`make this a project [(tracked)|(local)]`)

An existing store is reported (`store exists`), never recreated, restaged or re-decided. Inside a
git work tree, a brief with neither mode creates nothing and reports
`ask: tracked or local store?`. Otherwise create `.supervisor/` with its README per SKILL.md (in
the current directory when no project root exists) and write no entries. For `(local)`, append the
line `/.supervisor/` to `$(git rev-parse --git-path info/exclude)` unless
`git check-ignore -q .supervisor` already succeeds; never edit `.gitignore`. Then `git add
.supervisor` and do not commit (`git-ops` does); leave `VERSION` alone. Skip the staging and report
why for an untracked store (preamble) or while a merge, rebase or cherry-pick is in progress.

## Migrate (`migrate <path>`)

For `migrate docs/`:
- Live: `git mv` each `docs/plan-*.md` to `.supervisor/working/plans/` and each
  `docs/research-*.md` to `.supervisor/working/research/`, same name. Write no entries.
- Spent: for each `docs/archive/plan-*.md` and `docs/archive/research-*.md`, write one `decision`
  or `fact` entry per item that is still in force and passes the recording test (SKILL.md), one
  entry per item, never consolidated (`## Approach`, `## Decisions`, `## Scope Notes`, decided
  Open Questions, research conclusions), checking neighbours as in close-out step 3, with `source:
  .supervisor/archive/working/<plans|research>/<name>#<section>`; then `git mv` the file there.
  Move a file only after its entries exist. Propose lessons only.
- Every other `docs/` file stays; remove `docs/archive/` once empty.
- Report the moved paths, the entries written, and files outside `.supervisor/memory/`,
  `.supervisor/archive/` and `history.md` that still name a moved file (grep by name), then
  `recorded N`.

For a legacy writing rules file, skipping Standing Rules and Session Decisions already migrated
(check neighbours as in close-out step 3):
- Each Standing Rule bullet that passes the recording test becomes one `convention` entry
  (`domain: writing`, `source: .supervisor/archive/working/writing/writing-rules.md`).
- Each Session Decision Log entry that still binds (the test's binding condition) becomes a
  Session Decision in the draft-state file under `.supervisor/working/writing/` for the path part
  of its identifier, keyed as `references/writing.md` defines (create the
  file from the template when missing). When that path no longer exists, move the file to
  `archive/working/writing/` at once.
- Return each Pending Verification item as a promote-or-drop proposal.
- Then `git mv` the file to `.supervisor/archive/working/writing/writing-rules.md`.

## Archive (`archive <draft-state path>`)

`git mv` the state file to `.supervisor/archive/working/writing/`, keeping its name.

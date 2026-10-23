# Plan: stop memory-store bloat at write time and close-out

## Goal

Pack recording rules that keep a project store to extra information only. Five causes from this
repo's audit (66 live entries, about half redundant): duplicates of what the delivered work
encodes, plan-time one-offs, sibling entries, behaviour-restating bodies, stale roadmap text.
Non-goals: editing any `.supervisor/` entry or roadmap; new agents; entry frontmatter keys
(lint-fixed, `tests/test_pack_lint.py:199`); time-based expiry; merging entries.
Expected change: about 90-130 changed prose lines, mostly in project-memory `SKILL.md`,
`templates/entry.md`, `references/curator-procedures.md` and `pack/agents/curator.md`, a few in
`supervisor.md`, `plan-writing/SKILL.md:31` and `docs/architecture.md`. No code.

## Approach

One recording test in `project-memory`, cited by every curator procedure. Mid-plan decisions go
to the plan Log and reach memory only through the test at close-out. Add a retire outcome and an
on-request audit. Bulk distill and migrate (`b3db943`, `dc42e3d`) created 55 of the 66 entries,
so the test must govern them too.
Rejected: a dedupe hook (needs judgement; new machinery); changing the five-entry cap (it
bounds runs, not redundancy); an auditor agent (the curator owns curation); per-subject entries
and a threshold audit (user, 2026-10-22).

## Decisions

D1. Recording test, in SKILL.md `## Curation and writing` (:98-103). Write an entry only if:
(a) it binds work after the current plan closes; stage order, release grouping, the branch the
work ran on, and who confirms at which stage are one-offs and fail;
(b) the delivered work does not encode it (code, docs, config, tests, prose deliverables, the
project's instructions file); if the work encodes the rule, the entry holds only what the work
lacks (rationale, rejected options, user preferences, invisible facts), with the encoding file in
`affects:`; with nothing extra left, the candidate is a no-op;
(c) the body gives the choice and its why, not behaviour the `affects:` files show;
(d) if an entry on the same decision, rule or fact exists, supersede it instead of adding a
sibling.
Each entry justifies its own place. Entries are never merged or grouped (research D11 stands).
Generic wording only; no "pack".

D2. Principles, added after SKILL.md:8, which stays:
- memory holds extra information only, and every entry has a real cost (user, 2026-10-22);
- the store is the agents' memory: the user decides substance (what binds, what to remember or
  forget, lessons per :70) and never reviews entry text or approves an individual change;
- curation is internal housekeeping, reported as counts per outcome and kinds of cuts.

D3. `templates/entry.md:9` body: the choice in one or two sentences, then why and rejected
options; behaviour stays in the `affects:` files.

D4. Close-out (`curator-procedures.md:12-19`):
- step 2 filters candidates with D1, including the plan Log's `decision:` lines (D6);
- step 3 outcomes are new, supersede, retire or no-op, with neighbours also found by `affects:`
  overlap with the paths the plan changed;
- "Merge duplicates or contradictory entries on one subject" (:17-18) becomes "when two entries
  record one decision, supersede the older".
Retire, for an entry the delivered work now encodes with nothing extra left: add
`superseded by: <artifact path>`, move it to `archive/memory/<kind>/`, and write no replacement.
SKILL.md:62-66 gains this form, and its "newer of two merged entries" becomes "newer of two
entries recording one decision". Retires are not new entries and do not count toward the cap.
`curator.md:43` changes "write or retire one entry" to "write or supersede one entry", so that
"retire" has one meaning.

D5. Migrate (:81-105, sentences :86-87, :98, :100) and close-out step 6's legacy bullets
(:28-29) apply D1 to each item, without consolidating. Migrate stays uncapped. Record (:57) and
remember (:63) cite the test.

D6. The `decision:` line format lives in plan-writing:31: `- YYYY-MM-DD decision: <text>;
source: <user | lead>`. supervisor.md:81-83's "records as a memory entry ... `recorded N`"
becomes "logs each user answer or binding lead decision as a `decision:` Log line" (about 14
words in place of 21), and the clerk writes the line as briefed (`clerk.md:22`). Single-stage
runs keep curator `record` (:85-89). Repo follow-up for curator: supersede
`.supervisor/memory/decisions/2026-10-21-the-post-wave-clerk-records-mid-program.md`.

D7. supervisor.md:107-108 becomes "(push, publish, send; not memory curation)". With D6, the net
change is about -4 words against the 1000 cap; the executor confirms with `body_words`. The full
principle is D2, since supervisor does not preload project-memory.

D8. Roadmap (SKILL.md :119-122): Background states only the current gap, and items cite only the
entries that still bind. Close-out step 6 (:24-33) rewrites the Background of a partly landed
item, repoints citations of superseded entries to their replacements, and drops citations of
retired ones. `curator.md:20` ("only to remove landed items") widens to match.

D9. `audit` brief, a new `## Audit` section of 8-12 lines after the idle-plan sweep (:41-51). It
applies D1 and the staleness check to every live entry and roadmap citation. Outcomes are keep,
retire (D4), supersede, or drop. Drop is for a one-off that fails D1(a): add `dropped: audit
<date>` and archive the entry with no replacement (not Forget, which writes a retraction). One
line states that it never merges. Lessons and goals are only proposed for change. It is
cap-exempt like `migrate`, and it reports counts per outcome plus one line per kind of cut.

D10. curator is at 379/400: `audit` in the :16-18 brief list, the :32 cap line, retired and
dropped counts in the :49-53 report, the :20 widening, and a description addition at :3 ("audit
the store on request"; frontmatter, so uncapped). Shorten the new text, not existing rules, if
words run out. project-memory has 280 words of headroom.

## Outline

- `SKILL.md:100-102`: the procedure list adds `audit`.
- `docs/architecture.md`: :39 clerk row becomes "logs plan decisions as briefed"; :40 curator row
  adds audit and retire; :84 "The `clerk` records" changes to match, and its cap sentence adds the
  audit exemption.
- Measure word caps with the lint's `body_words`.

## Slices

Let `CP=pack/skills/project-memory/references/curator-procedures.md`.

1. Recording test on every curator write path. Units: A `SKILL.md` (:8, :62-66, :98-103);
   B `entry.md`; C `$CP` (:4-5, :12-19, :57, :63, :81-105).
   - `no merge: grep -rni merge pack/skills/project-memory | grep -v git -> only the D1 line (plus the Audit line after Slice 4)`
   - `cited: grep -c "recording test" $CP -> >=4`
   - `generic: git diff -U0 -- pack/skills/project-memory | grep '^+[^+]' | grep -w pack -> none`
   - Checkpoint: `python3 -m pytest -q`
2. Roadmap rule. Units: A `SKILL.md` :119-122; B `$CP` step 6; C `curator.md` (:20, :43).
   - `repoint: grep -n repoint $CP -> the step 6 line`
   - Checkpoint: `python3 -m pytest -q`
3. Mid-plan decisions via the Log. Units: A `supervisor.md` (:81-83, :107-108);
   B `plan-writing/SKILL.md:31`.
   - `routed: grep -ln "decision:" pack/agents/supervisor.md pack/skills/plan-writing/SKILL.md
     -> both`
   - `no entry: grep -n "records as a memory entry" pack/agents/supervisor.md -> none`
   - Checkpoint: `python3 -m pytest -q` (supervisor <=1000)
4. On-request audit. Units: A `$CP` `## Audit` and cap line; B `curator.md` (:3, :16-18, :32,
   :49-53); C `docs/architecture.md`; D `SKILL.md:100-102`.
   - `wired: grep -ln audit pack/agents/curator.md pack/skills/project-memory/SKILL.md
     docs/architecture.md -> all three`
   - `one no-merge line: sed -n '/^## Audit/,/^## [^A]/p' $CP | grep -ci merge -> 1`
   - `lessons safe: sed -n '/^## Audit/,/^## [^A]/p' $CP | grep -c lesson -> >=1`
   - Checkpoint: `python3 -m pytest -q && ./deploy install --dry-run`

## Verification

`python3 -m pytest -q` passes and `./deploy install --dry-run` is clean. In a read-through, each
cause maps to a rule: duplicates to D1(b) and retire; one-offs to D1(a), D6 and drop; siblings to
D1(d); behaviour bodies to D1(c) and D3; roadmap to D8.

## Risks

- A Sonnet curator over-applies D1(b). The "nothing extra left" condition, and archiving instead
  of deleting, bound the damage.
- Mid-plan decisions live only in the plan Log until close-out. The idle-plan sweep surfaces
  plans that never close.
- Existing stores keep their legacy entries until an audit runs.

## Scope Notes

In scope: the files in Goal. Out of scope: this repo's `.supervisor/`, including the
repo-convention follow-up (handled separately). User decisions not to reopen (2026-10-22): D1
(no merge, one entry per item), D2, D6, D9, generic wording.

## Assumptions

- No test greps curator brief names or headings: checked, `tests/test_pack_lint.py` has none.

## Open Questions

None.

## Log

## Todo

- [x] Slices 1-4, in order
- [x] Verification
- [ ] Repo follow-up for curator: supersede the post-wave-clerk entry (D6)

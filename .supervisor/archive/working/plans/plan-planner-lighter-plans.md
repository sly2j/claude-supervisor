# Plan: lighter plans from the planner

Research: the owner's notes (`research-lighter-plans.md`, scratchpad, 2026-10-21), cited below as
"research, <section>"; its Takeaways section is the target behaviour.

## Goal

Make `planner` produce plans a human can review in one sitting: decisions plus a signature-level
outline, phased as vertical slices with a test checkpoint each, with open questions asked before
the long plan is written. Make `critic`, `executor`, `executor-worker` and the docs consume that
shape.

Non-goals: researcher and writer workflows; memory beyond the curator's plan-reading gap; the
Work Packages mechanism (its block changes file, not content); `VERSION`; deploying; a new agent.

Expected change: about 290 lines (a 220-line skill, about 50 changed lines in `planner.md`,
about 20 lines across six other files). This plan stays under that.

## Approach

One new protocol skill, `plan-writing`, holds the plan format and its review checklist. `planner`
preloads it; `critic` loads it for domain `plan`, as it loads `science-writing-style` for prose
(`pack/agents/critic.md:46-47`). `planner.md` keeps workflow only: its artifact contract (contents
list, release naming, package block; 312 words) moves to the skill, and it gains a short
`## Questions First` step built on the existing blocked report (`lead-loop` section 7),
`Review: light`, and question batching (`supervisor.md:110-111`). `executor` runs each slice as
a wave. Rejected: rules in `lead-loop` (1131/1300 words; the other leads do not plan).

## Decisions

- D1 Home of the rules: `pack/skills/plan-writing/SKILL.md`, `user-invocable: false`, under 1300
  words and 300 lines. Skill: one more directory and one architecture row, format rules split
  from workflow rules. Trim instead: no new file, but the rules compress below usability and
  spend every future word in two capped files (2 and 0 words of headroom today). Owner approved
  2026-10-21, adding: every rule the critic reviews plans against lives in the skill;
  `planner.md` keeps workflow only (fan-out, questions first, review, annotation, report) (D10).
- D2 Sections of every plan, child plans included: `## Goal` (with non-goals and the expected
  change size), `## Approach`, `## Decisions`, `## Outline`, `## Slices`, `## Verification`,
  `## Risks`, `## Scope Notes`, `## Assumptions`, `## Work Packages` (when split; unchanged),
  `## Open Questions`, `## Log`, `## Todo`. `## Slices` replaces `## Orchestration`.
  `## Decisions` becomes mandatory, which closes the roadmap gap (`.supervisor/roadmap.md:37-39`)
  since close-out reads it (`curator-procedures.md:12-13`); `## Approach` stays, so migrate
  (l.82) needs no change.
- D3 The no-code rule, verbatim in the skill: "Do not write implementation code. Snippets are
  allowed only for non-obvious logic (a tricky algorithm, a migration), at 15 lines or fewer,
  marked as illustrative." Tests appear as a name plus its assertion; `executor` writes the
  bodies (research, "What a lighter plan should contain").
- D4 Phasing is vertical: a slice is a thin end-to-end change with its own test cases and a
  checkpoint command; "interfaces, then callers, then tests" is a review finding (research,
  "Vertical slices").
- D5 Length: a plan is never longer than the change it describes; `## Decisions` at most about
  200 lines; `## Outline` at most about two pages. `## Goal` states the expected change size so
  the critic can check the first rule (research, "Rough length targets").
- D6 Questions first, within existing mechanics: when the brief leaves an open question or a
  design fork, the first pass writes `## Goal`, `## Approach`, `## Decisions`, `## Open
  Questions` (each with a recommended answer) and the slice headings only, then returns Outcome
  `blocked`; `supervisor` batches the questions (`supervisor.md:110-111`) and the answers come
  back in a re-dispatch brief: the planner moves each answered item from `## Open Questions` to
  `## Decisions`, then writes the remaining sections. Owner answers 2026-10-21: the two-step
  runs only in that case (Q1); `supervisor.md` stays untouched (Q2); the first pass gets
  `Review: light` before it returns, and that round checks each open question: answerable from
  the repo, the research artifact or memory, or the user's? The planner answers the answerable
  ones itself, moves them to `## Decisions` with the evidence, and continues to the full plan;
  it returns `blocked` only with the questions that survive (Q3). The full plan keeps its usual
  round. Options considered: (A) this; (B) one pass with the questions left in `## Open
  Questions`, the status quo the research rejects; (C) the planner asks the user directly,
  bypassing the supervisor's single user channel; (D) a design stage in the package block,
  which reopens the six-field decision. Chosen: A.
- D7 `executor` treats each slice as a wave and runs the slice checkpoint before the next; a
  worker brief's plan excerpt is the slice's signatures, `file:line` pointers and test cases.
- D8 The critic's plan line delegates to the skill's reviewing section, which names the five
  violations from the contract plus feasibility, executable todos, research coverage, the
  package block schema, and the first-pass question check (D6).
- D9 No new lint test: the existing lint covers the skill (name, caps, `skills:` names) and
  the agent caps; the slice checkpoints below are greps plus the suite.
- D10 The six-field block, its Status values, the integration and child-plan shape lines
  (`planner.md:59-73`) and the release-naming rule (l.37-38) move to the skill verbatim; the
  judgment rules (l.56-58, 74-76: when to split, parallel preference, user override, `Amend
  parent:`, single approval) stay. The schema is still stated once; `README.md:87` points to
  the skill; the six-field memory entry's `affects:` is the curator's to update at close-out.

## Outline

Governing sentences are given where wording matters; the executor writes the rest.

`pack/skills/plan-writing/SKILL.md` (new; pattern: `pack/skills/lead-loop/SKILL.md:1-6`
frontmatter with `user-invocable: false`; reviewing section pattern:
`pack/skills/science-writing-style/SKILL.md:111-133`):
- `## Contents`: the D2 sections, one line each. `## Outline`: per file, the signatures and
  data shapes to add or change, `file:line` pointers to the pattern to follow, invariants and
  gotchas. `## Slices`: numbered slices, each with what it delivers end to end, its units
  (disjoint files), test cases as `name: input -> expected`, and a checkpoint command.
  `## Verification`: the end-to-end check after the last slice. `## Risks`: including failure
  modes the tests do not cover. `## Scope Notes`, `## Assumptions`, `## Open Questions`,
  `## Log`, `## Todo`: `planner.md:25-36` wording unchanged (`supervisor.md:83,85` and
  `curator-procedures.md:12` depend on it). First pass (D6): "A first pass holds `## Goal`,
  `## Approach`, `## Decisions`, `## Open Questions` (each with a recommended answer) and the
  slice headings only; on re-dispatch with answers, move each answered item to `## Decisions`
  and write the rest."
- `## Rules`: D3 verbatim; D4 ("Each slice is a thin end-to-end change with its own tests and
  checkpoint; never phase by layer."); D5 with the expected-change line; "A decision belongs in
  `## Decisions` or `## Open Questions`, never in `## Assumptions`."; pointers over pasted
  content (research, "What a lighter plan should contain"); the release-naming bullet
  (`planner.md:37-38`, verbatim).
- `## Work Packages`: `planner.md:59-73` verbatim (the fenced block is a schema, not a
  snippet), with `## Orchestration` read as `## Slices`.
- `## Reviewing plans (for critic)`: BLOCKING: implementation code (a fence with a body over
  15 lines, or an implementation body not marked illustrative; signature and data-shape fences
  are not snippets); a slice without test cases or a checkpoint; phasing by layer; a decision
  hidden as an assumption; more lines than the stated expected change; a path or pointer that
  does not exist; a package block missing a field or with a Status outside its three values.
  SHOULD: `## Decisions` over about 200 lines or `## Outline` over about two pages; a todo that
  cannot be executed without guessing; a research finding the plan ignores; a missing error,
  migration or compatibility case. First pass: "Review only the sections a first pass holds.
  For each open question, state whether it is answerable without the user and from what (the
  repo, the research artifact, memory); a design fork that existing constraints settle is a
  finding."

`pack/agents/planner.md`:
- Frontmatter `skills:` gains `plan-writing` after `lead-loop` (`planner.md:6-7`).
- `## Artifact` (l.14-39) keeps the path bullet (l.17-18) and the write-only bullet (l.39);
  the contents list and release bullet (l.19-38, 204 words) become "Contents, sections and
  length per `plan-writing`."
- `## Work Packages` (l.54-76) keeps l.56-58 and l.74-76; l.59-73 (108 words) become "Block
  schema and shape per `plan-writing`."
- New `## Questions First` after `## Fan-Out`, about 85 words: "When the brief leaves an open
  question or a design fork, write the first pass per `plan-writing` and run `Review: light`
  on it, briefing `critic` to say which questions the repo, the research artifact or memory
  already answer. Answer those yourself, move them to `## Decisions` with the evidence, and
  continue to the full plan. Return Outcome `blocked` only with the questions that survive; the
  report's next action is: answer them, then re-dispatch `planner`. Otherwise write the full
  plan in one pass."
- `## Review` (l.78-82): add "The first pass gets `Review: light`; the full plan one round."
- `## Final Output` (l.92-96): add "for a first pass, the surviving questions with a
  recommended answer each". Budget: 698 - 204 - 108 + 12 + 8 + 85 + 12 + 12 = 515 of 700.

`pack/agents/critic.md`: the plan line (l.40-42) becomes "**plan**: Load the `plan-writing`
skill and apply its reviewing section." (600 - 42 + 11 words).

`pack/agents/executor.md`: l.36-37 become "When the plan has `## Slices`, each slice is a wave:
dispatch its units in parallel, integrate, and run its checkpoint before the next slice; deviate
only when the code contradicts it, and note the deviation in the `Fan-out` line of the report."
l.41-43 become "Within a slice, implementation, tests and docs are separate units; a unit that
needs another's interface waits for it." l.44-45: the brief "carries the unit's plan excerpt
(the slice's signatures, `file:line` pointers and test cases) and the conventions to follow."
Headroom: 384 of 700.

`pack/agents/executor-worker.md` l.20-21: "Follow the plan excerpt in your brief: implement the
signatures it names at the pointers it gives, and write the bodies of the tests it lists. If it
is wrong or ambiguous in a way that changes the outcome, stop and report rather than redesign."
Headroom: 233 of 400.

`docs/architecture.md`: planner row (l.30) scope becomes "Lead: decision-and-outline plans in
.supervisor/working/plans/, questions first"; skills table (l.82-93) gains
`| plan-writing | planner (preloaded), critic | new |`; the chain at l.68 reads
"researcher -> planner (questions, then the plan) -> user approval -> executor"; l.56 unchanged.

`pack/skills/agent-authoring/SKILL.md`: Tiers row for planner (l.14) reads
"all; preload `lead-loop`, `plan-writing`". The lint reads only model and effort from that table.

`README.md:87`: "(field rules in `pack/agents/planner.md`)" becomes "(field rules in the
`plan-writing` skill)". Skill budget: about 750 of 1300 words.

## Slices

"The lint suite" below is `python3 -m pytest -q tests/test_pack_lint.py`, or
`uv run --with pytest python3 -m pytest -q ...` where python3 has no pytest (memory fact).

### S1 Format rules land and are enforced

Delivers: the skill, the planner preload, the critic delegation; a plan written under the rules
is reviewable against them.
Units: `pack/skills/plan-writing/SKILL.md`; `pack/agents/planner.md` (`skills:`,
`## Artifact`, `## Work Packages` only); `pack/agents/critic.md`.
Tests:
- lint_passes: `tests/test_pack_lint.py` -> all pass (skill name and caps, `skills:` names
  exist, planner under 700, critic under 600, lines under 100 chars).
- no_code_rule_verbatim: `grep -c "Do not write implementation code" SKILL.md` -> 1.
- block_stated_once: `grep -c "^- Owns:"` -> 0 in `planner.md`, 1 in `SKILL.md`.
- horizontal_example_gone: `grep -n "interfaces, then callers" pack/agents/planner.md` -> empty.
- critic_delegates: `grep -n "plan-writing" pack/agents/critic.md` -> one hit, on the plan line.
- reviewing_covers_five: grep the reviewing section for "15 lines", "layer", "checkpoint",
  "assumption", "expected change" -> each hits once.
Checkpoint: the lint suite.

### S2 Questions first

Delivers: the two-pass behaviour and its documentation.
Units: `pack/agents/planner.md` (`## Questions First`, `## Review`, `## Final Output`);
`docs/architecture.md` l.30 and l.68.
Tests:
- questions_first_present: `grep -c "## Questions First" pack/agents/planner.md` -> 1.
- blocked_only_survivors: `grep -c "questions that survive" pack/agents/planner.md` -> 1.
- light_round_named: `grep -c "Review: light" pack/agents/planner.md` -> at least 1.
- answerable_check: `grep -c "answerable without the user" SKILL.md` -> 1.
- orchestration_gone: `grep -rn "## Orchestration" pack/` -> empty.
- chain_documented: `grep -c "questions, then the plan" docs/architecture.md` -> 1.
Checkpoint: the lint suite (planner under 700).

### S3 Execution consumes slices

Delivers: executor waves by slice; worker briefs carry signatures, pointers and tests.
Units: `pack/agents/executor.md`; `pack/agents/executor-worker.md`.
Tests:
- slices_drive_waves: `grep -c "## Slices" pack/agents/executor.md` -> 1;
  `grep -n "interfaces first" pack/agents/executor.md` -> empty.
- excerpt_shape: `grep -c "test cases" pack/agents/executor.md` -> 1;
  `grep -c "bodies of the tests" pack/agents/executor-worker.md` -> 1.
Checkpoint: the lint suite.

### S4 Inventory sync and self-check

Delivers: the architecture and tier tables name the skill; this plan passes its own rules.
Units: `docs/architecture.md` (skills table); `pack/skills/agent-authoring/SKILL.md` l.14;
`README.md` l.87.
Tests:
- skill_row: `grep -c "plan-writing" docs/architecture.md` -> 1 (the skills-table row).
- tier_row: grep agent-authoring `SKILL.md` for the backticked pair "`lead-loop`, `plan-writing`"
  -> 1.
- readme_pointer: `grep -c "plan-writing" README.md` -> 1; `grep -c "planner.md" README.md`
  -> 0.
- self_check: this file -> `wc -l` under 290, no fence over 15 lines, every `### S` block
  has a Tests list and a Checkpoint line.
Checkpoint: full suite.

## Verification

1. Full suite green: `python3 -m pytest -q` (or the `uv run` form).
2. `./deploy install --dry-run` validates every skill directory (`agent-authoring` l.73-77).
3. Apply the skill's `## Reviewing plans` checklist to this plan file by hand: no BLOCKING item.
4. The first real planning task after the merge is the smoke test: its first pass must stop
   with questions when the brief has any (not executable here).

## Risks

- A `blocked` planner report could be routed to `executor` by a supervisor reading only the
  chain (`supervisor.md:52-53`); the report's next-action line (D6) is the guard.
- Archived plans keep `## Orchestration`; nothing reads it after this change (sweep: no other
  consumer in `pack/` or `docs/`).
- Not covered by the checks: the planner still drifts to code. The critic's BLOCKING item is
  the backstop; the research notes the drift is unmeasured.

## Scope Notes

- In: the files named in `## Outline` (`README.md` l.87 only). Out: `planner-worker.md`,
  `scope-critic.md` (the sweep found no plan-specific rule in it), `supervisor.md` (D6),
  `curator-procedures.md` (D2), `lead-loop/SKILL.md`, tests under `tests/` (D9), memory
  entries (curator's job), `VERSION`, deploying, researcher and writer workflows.
- Decisions `executor` must not reopen: reach is product behaviour, every rule in `pack/`
  (`.supervisor/memory/conventions/2026-10-21-the-pack-is-standalone-behaviour-lives-in.md`);
  the 15-line illustrative cap; vertical slices; questions first; no new agent type; the
  entries under `.supervisor/memory/decisions/` on the six-field block, plans never nest,
  planner decides splits, and supervisor runs packages as a program (all dated 2026-10-21);
  no cap raise without the owner (`.supervisor/roadmap.md:17-19`).
- Feature branch: never touch `VERSION`; rebase on `main` before the squash merge (CLAUDE.md).

## Assumptions

- The lint reads only `(model, effort)` from the Tiers table and requires only `lead-loop` in a
  lead's `skills:` (`tests/test_pack_lint.py:28-30,110-116`); a second skill passes. Checked by S1.
- `critic` loads a skill named in prose, as for prose reviews (`critic.md:46-49`). Checked by
  reading; no mechanism change.
- `supervisor` forwards a lead's questions without new text (`supervisor.md:110-111`) and the
  answers re-run the stage (`supervisor.md:87`; the report's next action for flat requests).
  Checked by `## Verification` item 4.

## Open Questions

None open: Q1-Q3 were answered by the owner on 2026-10-21 and folded into D1, D6 and D10.

## Log

- 2026-10-21 planner: annotation cycle; D1 approved with the move-to-skill addendum (D10),
  Q1-Q3 answered (first pass gets `Review: light`, which may unblock); deferred: none
- 2026-10-21 executor: done, S1-S4 landed (plan-writing skill, planner/critic/executor docs
  sync), suite 367 passed 6 skipped, critic PASS; deferred: Verification 4 (first real planning
  run is the smoke test)

## Todo

- [x] S1: write `pack/skills/plan-writing/SKILL.md` (contents, rules, package block, reviewing
      section); preload it in `planner.md` and replace its contents list and package block
      with pointers; replace the critic plan line; lint.
- [x] S2: add `## Questions First`, the `## Review` sentence and the Final Output clause to
      `planner.md`; update `docs/architecture.md` l.30 and l.68.
- [x] S3: edit `executor.md` l.36-45 and `executor-worker.md` l.20-21.
- [x] S4: skills table row in `docs/architecture.md`; Tiers row in `agent-authoring`;
      `README.md` l.87; full suite; `./deploy install --dry-run`; self-check this plan.

---
name: plan-writing
description: Plan artifact contract for the Supervisor for Claude pack - sections, the no-code rule, vertical slices, length targets, the work-package block, and the checklist critic reviews plans against. Preloaded by planner; loaded by critic for domain plan. Not for direct use.
user-invocable: false
---

# Plan Writing

A plan holds the decisions the implementer cannot make alone, not the code (Superpowers
writing-plans skill). A short plan gets reviewed; a long one gets skimmed (Horthy, HumanLayer).

## Contents

Every plan, child plans included, has these sections:

- `## Goal`: the goal, non-goals, and the expected change size.
- `## Approach`: the approach, with rationale and rejected alternatives in one line each.
- `## Decisions`: each decision with its reason; the part the user reads closely.
- `## Outline`: per file, the signatures and data shapes to add or change, `file:line`
  pointers to the pattern to follow, invariants and gotchas.
- `## Slices`: numbered slices, each with what it delivers end to end, its units (disjoint
  files), test cases as `name: input -> expected`, and a checkpoint command. `executor` runs
  the slices in order, units in parallel within one.
- `## Verification`: the end-to-end check after the last slice.
- `## Risks`: risks, compatibility concerns, and failure modes the tests do not cover.
- `## Scope Notes`: what is in and out of scope, and decisions the user made that
  `executor` must not reopen, citing memory entries by file where they exist
- `## Assumptions`: one line each, with how it is checked
- `## Work Packages` (rules below), when the work splits into packages
- `## Open Questions` for decisions that belong to the user, never hidden assumptions
- `## Log`: one line per lead dispatch (date, package or lead, outcome, deferrals and why), from
  the lead's report, appended by `fixer`; leave it empty. It also holds decision lines, one per
  user answer or binding lead decision, in the exact format
  `- YYYY-MM-DD decision: <text>; source: <user | lead>`, appended by `fixer` as briefed and
  reaching memory only through curator close-out
- a granular `## Todo` checklist

A first pass holds `## Goal`, `## Approach`, `## Decisions`, `## Open Questions` (each with a
recommended answer) and the slice headings only; on re-dispatch with answers, move each
answered item to `## Decisions` and write the rest.

## Rules

- Do not write implementation code. Snippets are allowed only for non-obvious logic (a tricky
  algorithm, a migration), at 15 lines or fewer, marked as illustrative. Tests appear as a name
  plus its assertion; `executor` writes the bodies.
- Each slice is a thin end-to-end change with its own tests and checkpoint; never phase by
  layer. Models default to horizontal plans that cannot be exercised until the end (Horthy,
  "Why Software Factories Fail").
- A plan is never longer than the change it describes; `## Goal` states the expected change
  size so the critic can check. `## Decisions` is at most about 200 lines and `## Outline` at
  most about two pages.
- A decision belongs in `## Decisions` or `## Open Questions`, never in `## Assumptions`.
- Point instead of pasting: `file:line` pointers and research-artifact names carry context
  cheaply (Anthropic, effective context engineering).
- Plans name a major release (`2.x`), stage, package or "next minor", never a minor
  version: minors move as work lands.

## Work Packages

- One block per package, listing only the stages it needs:

```
### P1: <name>
- Goal: <one sentence>; done when <criterion>
- Owns: <files or area, disjoint across packages>
- Deps: none | <package ids>
- Stages: <ordered subset of research, plan, execute, write>
- Status: <stage due next> | blocked: <stage>: <why> | done
- Artifacts: <research-<topic>-<id>.md or plan-<topic>-<id>.md at the default paths, a draft
  path, or ->
```

- Integration work is a package too; a parent plan's `## Slices` and `## Todo` point here.
- A child plan is a normal plan for one package at the briefed path, with no `## Work Packages`.

## Reviewing plans (for critic)

BLOCKING:
- implementation code: a fence with a body over 15 lines, or an implementation body not marked
  illustrative (signature and data-shape fences are not snippets)
- a slice without test cases or a checkpoint
- phasing by layer (interfaces, then callers, then tests)
- a decision hidden as an assumption
- more lines than the stated expected change
- a path or pointer that does not exist
- a package block missing a field or with a Status outside its three values

SHOULD:
- `## Decisions` over about 200 lines or `## Outline` over about two pages
- a todo that cannot be executed without guessing
- a research finding the plan ignores
- a missing error, migration or compatibility case

First pass: review only the sections a first pass holds; bare slice headings are expected there,
not a finding. For each open question, state whether it is answerable without the user and from
what (the repo, the research artifact, memory); a design fork that existing constraints settle is
a finding.

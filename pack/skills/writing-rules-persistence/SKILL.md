---
name: writing-rules-persistence
description: Schema, precedence model, and override semantics for a project's docs/writing-rules.md, the per-project file that carries writing decisions (Standing Rules, per-draft Session Decisions, Pending Verification) across sessions. Use whenever a writing task runs in a project that has or should have docs/writing-rules.md - drafting, revising, or reviewing prose under project rules, resolving a conflict between a style rule and a project rule, recording a per-draft decision, promoting a pattern to a Standing Rule, or creating the file from the template.
---

# Writing-rules persistence

Canonical reference for `docs/writing-rules.md` in the project root. Used by the `writer` lead,
`writer-worker`, and `critic` (when reviewing prose). This skill defines persistence semantics
only; the style rules themselves live in `science-writing-style` or `presentation-style`.

## File schema

Plain Markdown with exactly these three top-level sections, each appearing once:

- `## Standing Rules`: durable project constraints, optionally grouped into `###` categories.
  Recommended: Voice and tone, Banned vocabulary, Project terminology, Framing principles,
  Workflow conventions.
- `## Session Decision Log`: decisions scoped to one draft. Each entry header is
  `### YYYY-MM-DD - <draft identifier>`, followed by bullets. Entries never generalize beyond
  their draft.
- `## Pending Verification`: a flat bullet list of observed patterns awaiting a user decision.

## Precedence stack

Highest priority first:

1. Hard-floor rules in the style skill. Never overridden.
2. Standing Rules in `docs/writing-rules.md`.
3. Active Session Decisions for the current draft.
4. Author samples.
5. Overridable defaults in the style skill.

A critic suppresses a finding when the pattern matches a Standing Rule or active Session Decision
(unless a hard floor is violated) and reports the suppression with its source.

## Session Decision matching

- The `writer` lead fixes a `current draft identifier` for the task (a file path such as
  `body.tex`, optionally with a section, or an inline tag) and passes it to every worker and critic.
- A Session Decision is active only when the identifier in its header matches the current draft
  identifier exactly, byte for byte, including any leading `./`. The date does not participate.
- If more than one entry matches the same identifier exactly, treat the active set as empty and
  surface the ambiguity to the user.
- Near-miss detection is diagnostic only. Compare after stripping a leading `./`, collapsing
  whitespace, and comparing basenames; surface likely typos to the user, but never activate a
  normalized-only or basename-only match.

## Structural validation

The file is malformed when any of the three top-level sections is missing or duplicated, a Session
Decision header does not follow `### YYYY-MM-DD - <draft identifier>`, or Pending Verification is
not a flat bullet list. Standing Rules subsections are optional.

When malformed: do not apply any of its rules, continue under the style skill alone, and tell the
user which sections are broken.

## Pending Verification

Watch-list items, never binding.

- A critic must not suppress a finding because the pattern is listed here; it may raise a matching
  pattern as minor with a `watchlist` note.
- A writer-worker does not enforce these entries unless the `writer` lead turns one into an explicit
  instruction for this task.
- The `writer` lead may surface recurring items as promotion candidates.

## Read protocol

- The `writer` lead locates the file, runs the structural check, selects active Session Decisions,
  flags any conflict between the user's request and a Standing Rule before dispatching, and passes
  workers and the critic: the rules-file path (or `none`), the current draft identifier, the active
  Session Decisions (or `none`), and the style skill to load.
- Workers and the critic use the path they are given and do not search for another file. `none`
  means no project rules apply.

## Writing to the file

- Workers and the critic never edit `docs/writing-rules.md`.
- The `writer` lead proposes changes and applies them only after the user approves each one.
- After a draft is accepted or the loop stops, the `writer` lead may propose Standing Rule
  promotions: deviations from style defaults that were preserved across rounds (from overrides
  and preserved passages; recurring Pending Verification items are optional). For each candidate:
  - `pattern observed:` short description plus example text from the draft
  - `recommended subsection:` e.g. `Standing Rules > Voice and tone`
  - `suggested rule wording:` the bullet to add, verbatim
  - `override that preserved it:` the Standing Rule, Session Decision, or author-sample anchor

  Ask the user to confirm or reject each candidate individually.
- When the user resolves a repeated finding by suspending a rule for one draft, record it as a new
  Session Decision entry whose header uses the exact current draft identifier.

## Template

To create the file, copy `${CLAUDE_SKILL_DIR}/templates/writing-rules.md` to
`docs/writing-rules.md` in the project root (with user approval), then replace the placeholder
bullets with project entries and delete subsections that do not apply.

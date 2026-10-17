---
name: writing-rules-persistence
description: Schema, precedence model, and override semantics for a project's docs/writing-rules.md, the per-project file that carries writing decisions (Standing Rules, per-draft Session Decisions, Pending Verification) across sessions. Use whenever a writing task runs in a project that has or should have docs/writing-rules.md - drafting, revising, or reviewing prose under project rules, resolving a conflict between a style rule and a project rule, recording a per-draft decision, promoting a pattern to a Standing Rule, or creating the file from the template.
---

# Writing-rules persistence

Persistence semantics for `docs/writing-rules.md` in the project root, used by `writer`,
`writer-worker`, and `critic` (when reviewing prose). Style rules live in `science-writing-style`
and `presentation-style`.

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

## Worker procedures (writer-worker and critic)

The `writer` lead's brief gives you:

- the rules-file path, or `none`
- the current draft identifier
- the active Session Decisions, or `none`
- the style skill to load

Then:

- Use only the path you are given and do not search for another file. `none` means no project
  rules apply.
- Apply the active Session Decisions exactly as given.
- Treat Pending Verification entries as non-binding. A `writer-worker` does not enforce one unless
  the lead turns it into an explicit instruction for this task. A critic does not suppress a
  finding because the pattern is listed there; it may raise a matching pattern as minor with a
  `watchlist` note.
- Never edit `docs/writing-rules.md`.

## Lead procedures

The `writer` lead reads `${CLAUDE_SKILL_DIR}/references/lead-procedures.md` before dispatching,
and again when promoting rules or creating the file. A critic running without a lead (an ad-hoc
review) reads it for Session Decision matching.

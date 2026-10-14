# Lead procedures for `docs/writing-rules.md`

Lead-only procedures for the `writer` lead. The schema, precedence stack, and worker procedures
are in the skill's `SKILL.md`.

## Read protocol

Before dispatching:

- Locate `docs/writing-rules.md` in the project root and run the structural check below.
- Select the active Session Decisions with the matching rules below.
- Flag any conflict between the user's request and a Standing Rule to the user.
- Pass workers and the critic the four inputs listed under "Worker procedures" in `SKILL.md`: the
  rules-file path (or `none`), the current draft identifier, the active Session Decisions (or
  `none`), and the style skill to load.

## Session Decision matching

- Fix a `current draft identifier` for the task (a file path such as `body.tex`, optionally with
  a section, or an inline tag) and pass it to every worker and critic.
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

## Writing to the file

- Propose changes and apply them only after the user approves each one.
- After a draft is accepted or the loop stops, you may propose Standing Rule promotions:
  deviations from style defaults that were preserved across rounds (from overrides and preserved
  passages; recurring Pending Verification items are optional). For each candidate:
  - `pattern observed:` short description plus example text from the draft
  - `recommended subsection:` e.g. `Standing Rules > Voice and tone`
  - `suggested rule wording:` the bullet to add, verbatim
  - `override that preserved it:` the Standing Rule, Session Decision, or author-sample anchor

  Ask the user to confirm or reject each candidate individually.
- When the user resolves a repeated finding by suspending a rule for one draft, record it as a new
  Session Decision entry whose header uses the exact current draft identifier.

## Creating the file

Copy the skill's `templates/writing-rules.md` to `docs/writing-rules.md` in the project root (with
user approval), then replace the placeholder bullets with project entries and delete subsections
that do not apply. The skill directory is the parent of this `references/` directory.

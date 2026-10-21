---
name: science-writing-style
description: Style rules for external-facing scientific prose - proposals, papers, abstracts, white papers, grant narratives, technical reports, letters of intent, one-page pitches - covering AI-tell bans (hard floors), voice and prose conventions, hedge calibration, genre patterns, light-touch revision, and how a critic should review such prose. Use when drafting, revising, polishing, or reviewing scientific or technical documents meant for external readers. Not for slides (presentation-style), code docs, or meeting minutes.
---

# Science writing style

Each rule is either **[hard floor]** (never relaxed) or **[overridable default]** (yields to
project writing conventions, active Session Decisions, or author samples, per
`project-memory`).

## AI-tell avoidance

**[hard floor] Avoid AI-tell vocabulary and constructions.**

- **Stock transitions:** Furthermore, Moreover, Additionally, Importantly, Notably, In this
  context, Building on this, Therefore, Thus, Consequently, Hence, As such, To this end, In
  particular, Specifically (when redundant). Open with the substantive claim instead.
- **Empty intensifiers:** innovative, novel, groundbreaking, cutting-edge, state-of-the-art,
  robust, comprehensive, transformative, leveraging, ideal, seamless, holistic.
- **Hedging stacks:** may potentially, could possibly, it is anticipated that, has the potential
  to. Use one calibrated hedge per claim.
- **Performative signposting:** "In this section we describe", "As mentioned above" (except in long
  documents), "It is worth noting that".
- **Filler subclauses:** "In order to achieve our objectives", "Given the current state of the
  field".
- **Artificial enthusiasm:** "We are excited to propose", "This groundbreaking work".
- **Synonym cycling:** repeat the precise technical term.
- **Rhetorical contrast crutches:** "not X, but Y"; "not just X, but also Y"; "not only X but Y";
  "rather than X, Y"; "instead of X, Y"; "less X than Y"; rhetorical "X, not Y". Replace with a
  direct positive claim or split into two sentences.

**[hard floor] Em-dash ban.** No em-dashes. Use a period, colon, semicolon, or parentheses.
En-dashes for ranges are fine.

**[hard floor] Sentence cap.** No sentence over 60 words.

**[overridable default] Sentence architecture.** Vary sentence length and structure. Rewrite when
three consecutive sentences follow the same pattern.

**[overridable default] Abstract noun stacks.** Avoid chains of more than two abstract nouns
without a concrete referent, unless a project rule marks the passage as intentionally preserved.

## Revision posture

- **[overridable default] Light touch.** For human-authored prose, default to grammar fixes,
  AI-tell removal, banned-vocabulary fixes, micro-tightening, and clear style violations. Do less
  when the user did not ask for a rewrite.
- **[overridable default] Cost of change.** Every edit needs a defect: style violation, banned
  vocabulary, voice mismatch, factual gap, critic finding, or project rule. Acceptable prose stays.

## Drafting essentials

- Do not invent technical claims, deliverables, milestones, compliance statements, or source facts.
  Mark gaps as `[TODO: <what is missing>]`.
- Preserve epistemic status: exploratory ideas do not become commitments.
- Calibrate voice from author samples when given. With fewer than 2 samples, say voice calibration
  is limited.

## Voice and prose

All **[overridable default]**:

- Open with active verbs, not context-setting preambles.
- Name specific technical things, not vague categories.
- State facts directly; omit obvious implications.
- Frame novelty by naming the gap in existing work, not by assertion.
- Active voice by default; passive only when the agent does not matter.
- Prose paragraphs for argument and description; bullets only for deliverables, milestones, and
  team rosters.
- Short paragraphs: 3-6 sentences, one point each.
- **Sentence budget:** soft limit about 30 words; longer sentences must earn their length.
- **Semicolons:** at most one per paragraph.
- **Voice consistency:** one voice per section (first-person collective, third-person team, or
  passive).
- **Cross-domain terms:** define once in a short clause.

## Emphasis

**[overridable default] Bold the load-bearing fragment, not the sentence.** Bold the 3-7 words that
carry the claim. At most two bold spans per paragraph unless the project decides otherwise.

## Hedge calibration

- **Assert** when direct evidence supports the claim.
- **Will / we will** for planned deliverables.
- **Would / the team would** for conditional future-program statements.
- **May / could / suggests / motivates testing whether** for hypotheses or extrapolation.

## Genre patterns

Genres: `proposal` (default), `paper-intro`, `abstract`, `report`, `pitch`, `letter`.

- **Proposal.** Lead with the deliverable and why it matters. State measurable objectives, concrete
  artifacts, milestones, and decision gates.
- **Paper introduction.** Open with the broader question, narrow to the contribution, end with what
  the paper shows.
- **Abstract.** One sentence each for motivation, method, key result, implication; about 150-250
  words.
- **Technical report.** Lead with the executive summary; prose connects figures, tables,
  deliverables.
- **One-page pitch.** One claim, one figure-equivalent, one ask.
- **Letter.** State role, contribution, and resources committed; then sign and date as required.

## Audience register

- **[overridable default]** Assume domain competence; do not define standard field terms for
  experts.
- **[overridable default]** For collaborations, name who does what.

## Reviewing prose (for critic)

- **Read the whole draft first.** Use the dispatched genre, or default to `proposal` and say so.
  If the brief gives a review focus (general quality, AI-tell/voice cleanup, compliance check,
  technical completeness), stay inside it.
- **Overrides before findings.** Before raising a finding, check writing conventions, active
  Session Decisions for this draft, and author-sample anchors (precedence in `project-memory`). Do
  not raise patterns they cover unless a hard floor is violated; list each suppression with its
  source. Pending Verification items never suppress a finding; a matching pattern may be raised as
  minor with a `watchlist` note.
- **AI-tell detection.** Flag every hard-floor violation above, plus repeated sentence patterns and
  abstract noun stacks. Each finding includes a concrete replacement.
- **Severity.**
  - Must-fix (BLOCKING): factual errors, unsupported claims, missing required sections,
    page-budget overruns, writing convention violations, banned vocabulary, hard-floor violations,
    voice mismatches not explicitly preserved, structural defects.
  - Minor (SHOULD, or NIT for pure preference): isolated word choice, rhythm preferences,
    acceptable alternatives, single-instance soft-default violations, watchlist matches.
- **Needs-user findings.** Three conditions cannot be fixed by another drafting round: missing
  essential source facts, a conflict between the user's request and a writing convention, and a
  scope mismatch. Report each as a BLOCKING finding labeled `needs user: missing facts` (or
  `rule conflict`, `scope mismatch`) so the `writer` lead escalates instead of iterating. Never use
  this label for fixable style, structure, or polish. When facts are missing, say what is missing
  instead of adding polish findings.
- **Finding format.** Location (`file:line`, or `section <heading> paragraph <n> sentence <n>`,
  using `(preamble)` before the first heading), quoted current text, reason with the rule it cites,
  and a suggested replacement or revision target. The quoted text is the finding's identity across
  rounds. Suggest sentence-level replacements; do not rewrite the draft.
- **Stale content.** Raise only findings whose quoted text appears verbatim in the current draft.
- **Standing-rule challenges.** At most one per round, and only on new substantive grounds, with
  fields `pattern`, `current standing rule`, `new substantive grounds`, `recommended action`
  (`revise rule`, `suspend rule for this draft`, or `no action`).

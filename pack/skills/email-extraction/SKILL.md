---
name: email-extraction
description: Extract structured substance from an email thread - participants, ask/response chain, topic-grouped facts, actions with owners and timing, commitments, decisions, deadlines, unresolved questions - as a neutral intermediate artifact. Use when an email thread (pasted, .eml, exported mailbox text) must be digested before a reply, summary, task list, or status note is written, or when asked "what was asked / who owes what / what's still open" in a thread. Not for meeting transcripts (meeting-summary) or reference documents (document-extraction).
---

# Email extraction

Extract the recall-worthy substance of an email thread into a compact artifact that a downstream
writer maps into its own format.

## Scope

- Extract content only. Do not choose templates, presentation style, file destinations, or final
  prose. Do not edit files or insert notes.
- Meeting transcripts: use `meeting-summary`. Reference documents: use `document-extraction`.

## Rules

- Input is the raw thread plus optional vocabulary or domain context. Use the vocabulary to correct
  plausible name, acronym, or term errors.
- Prefer explicit statements over inferred intent; label uncertain or inferred items.
- Deduplicate points repeated across quoted replies.
- Identify who initiated, who responded, what was requested, and what remains unresolved.
- Group by topic when the thread covers several subjects.
- Capture actions with owner, task, and timing when stated.
- Include RAID items (risk, action, issue, assumption, dependency, decision) only when explicitly
  present, each in exactly one category. Do not force RAID onto informational or social mail.
- Omit pleasantries, signatures, disclaimers, and forwarding boilerplate.

## Fields

- **Thread metadata**: sender(s), recipient(s), date(s), subject, message count, date range.
- **Thread direction**: summary of the ask chain and response chain.
- **Topic groups**: ordered subjects, each with its own requests, decisions, actions, or issues.
- **Notes**: 1-4 factual bullets per topic.
- **Actions**: owner, task, timing, source topic.
- **Commitments**: explicit promises with owner and timing.
- **Decisions**: what was decided and by whom.
- **Deadlines**: what is due and when.
- **Unresolved questions**: unanswered or ambiguous questions.
- **RAID items**: only when explicitly present.
- **Ambiguities**: unclear references, names, dates, owners, conflicting statements.

## Edge cases

- Too sparse: say what is missing.
- Ambiguous identity, ownership, or timing: keep the ambiguity visible.
- Messages that conflict: extract both positions and note the conflict.

## Output

A compact two-layer artifact, factual and free of presentation markup:

- **Thread level**: metadata, direction summary, global ambiguities.
- **Per topic group** (in order): label, notes, actions, commitments, decisions, deadlines,
  unresolved questions, RAID (only when warranted), local ambiguities.

Before returning, check that every item traces to the thread or is labeled uncertain, that
reply-chain duplicates were merged, and that topic notes are not a message-by-message log.
